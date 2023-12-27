"""
Preprocess and save plant and residuals data for TEP.

- Note there are less model files than plant files, so they will be repeated to
generate residuals from all the plant files.
- It is assumed that input data has one-hot labels (columns) of the shape
IDV(0), IDV(2)... We simplify it decoding it into the traditional single
'fault' column.
- Used both for SHORT and LONG files.
"""
import os
import numpy as np
import pandas as pd
from MLdetect.utils import even_dfs, one_hot_decoder


sps = [2.837347, 7.566228]
sample_time = 36


def loop_plant_model_data(pulse_type):
    # Prepare file lists
    plant_file_list = [
        file for file in os.listdir(plant_dir)
        if file.endswith('.csv') and file.startswith(f'plant_{pulse_type}')]
    model_file_list = [
        file for file in os.listdir(model_dir)
        if file.endswith('.csv') and file.startswith(f'model_{pulse_type}')]
    model_idx = 0

    # Loop over plant files and pair with a model case at a time
    for plant_file in plant_file_list:
        # File and name handling
        model_filepath = os.path.join(model_dir, model_file_list[model_idx])
        assert os.path.isfile(model_filepath)
        plant_filepath = os.path.join(plant_dir, plant_file)
        assert os.path.isfile(plant_filepath)
        # Call plant/residual preprocessor
        preprocess_data_tep(plant_filepath, model_filepath, dst_dir=dst_dir,
                            pulse_type=pulse_type)
        # Loop over model files
        model_idx += 1
        if model_idx >= len(model_file_list):
            model_idx = 0


def preprocess_data_tep(plant_filepath, model_filepath, dst_dir, pulse_type):
    """
    Calculate residuals from single case plant and model data. Expects one-hot
    encoded labels.
    For the TEP case, align simulation timestamping based on SP(1).
    Save to files:
        - plant file
        - residual file
    """
    expected_n_cols = 228

    # Prepare file paths
    case_name = '_'.join(plant_filepath.split(os.sep)[-1].split('_')[1:])
    model_filename = model_filepath.split(os.sep)[-1]
    plant_dst_filepath = os.path.join(dst_dir, 'plant', f'plant_{case_name}')
    model_dst_filepath = os.path.join(dst_dir, 'model', model_filename)
    res_dst_filepath = os.path.join(dst_dir, 'residuals', f'res_{case_name}')

    # Load data
    plant_data = pd.read_csv(plant_filepath, index_col='Time')
    assert len(plant_data.columns) == expected_n_cols
    model_data = pd.read_csv(model_filepath, index_col='Time')
    assert len(model_data.columns) == expected_n_cols

    # Check SP(1) first rows are as expected
    for sp_col, path_ in zip([plant_data['SP(1)'], model_data['SP(1)']],
                             [plant_filepath, model_filepath]):
        filename = path_.split(os.sep)[-1]
        # Check starting setpoint is right for trimming
        if not np.isclose(sp_col.iloc[0], sps[0]) \
                and "idv0_0000" not in filename:
            print(f"SP(1) starts at unexpected value {sp_col.iloc[0]} in file "
                  f"{filename}")

    # For both dataframes, identify the number of consecutive SP1 rows=sps[0]
    # and trim the dataframes to that length
    for df in [plant_data, model_data]:
        trim_df(df)

    # Accumulate XMEAS(3) to XMEAS(9) since the model only has one
    accumulate_perm(plant_data)

    # Rescale and center model data to match plant data
    scale_model_data(model_data, pulse_type)

    # Generate residuals
    res_data, labels = gen_residuals(model_data, plant_data)

    # Write plant and residuals
    if os.path.isfile(plant_dst_filepath):
        print(f'WARNING: File {plant_dst_filepath} already exists. '
              f'Skipping file!')
    else:
        plant_data.to_csv(plant_dst_filepath)
    if os.path.isfile(res_dst_filepath):
        print(f'WARNING: File {res_dst_filepath} already exists. '
              f'Skipping file!')
    else:
        res_data.to_csv(res_dst_filepath)
    if os.path.isfile(model_dst_filepath):
        print(f'WARNING: File {model_dst_filepath} already exists. '
              f'Skipping file!')
    else:
        model_data.to_csv(model_dst_filepath)


def accumulate_perm(plant_data):
    """
    Accumulate XMEAS(3) to XMEAS(9) in plant data since the model only has one.
    """
    perm_cols = [f'XMEAS({i})' for i in range(3, 10)]
    perm_clean_cols = [f'XMEAS({i})_clean' for i in range(3, 10)]
    nan_cols = [f'XMEAS({i})' for i in range(4, 10)] \
        + [f'XMEAS({i})_clean' for i in range(4, 10)]
    plant_data['XMEAS(3)'] = plant_data[perm_cols].sum(axis=1)
    plant_data['XMEAS(3)_clean'] = plant_data[perm_clean_cols].sum(axis=1)
    plant_data[nan_cols] = np.nan


def trim_df(df):
    """ Trim dataframe to the number of consecutive SP(1). """
    sp1 = df['SP(1)']
    n_consecutive = 0
    for i in range(len(sp1)):
        if np.isclose(sp1.iloc[i], sps[0]):
            n_consecutive += 1
        else:
            break
    df.drop(df.index[:n_consecutive], inplace=True)


def scale_model_data(model_data, pulse_type):
    """ Scale and center model data to match mean and std of plant data. """
    # Scale model data to match plant data
    plant_data = None
    if pulse_type == "short":
        plant_data = ref_plant_data_short
    elif pulse_type == "long":
        plant_data = ref_plant_data_long
    for col in plant_data.columns:
        if model_data[col].std() == 0 or plant_data[col].std() == 0:
            continue
        model_data[col] = (model_data[col] - model_data[col].mean()) \
            / model_data[col].std() * plant_data[col].std() \
            + plant_data[col].mean()


def gen_residuals(model_data, plant_data):
    # Even dataframes and set the same time index
    even_dfs(plant_data, model_data)
    times = np.arange(sample_time, sample_time * (len(plant_data) + 1),
                      sample_time)
    for df in [plant_data, model_data]:
        df.index = times
        df.index.names = ['Time']
    # Separate features and labels
    label_cols = [col for col in plant_data.columns if col.startswith('IDV(')]
    feature_cols = [col for col in plant_data.columns if col not in label_cols]
    res_data = plant_data[feature_cols] - model_data[feature_cols]
    # Do one-hot decoding for labels to reduce columns
    labels = one_hot_decoder(plant_data[label_cols])
    # Remove one-hot encoded columns from plant data
    plant_data.drop(columns=label_cols, inplace=True)
    # Append label to both dataframes
    res_data['fault'] = labels
    plant_data['fault'] = labels
    return res_data, labels


def preprocess_plant_data(plant_filepath):
    """ Preprocess plant data to be used as reference for scaling. """
    plant_data = pd.read_csv(plant_filepath, index_col='Time')
    trim_df(plant_data)
    accumulate_perm(plant_data)
    return plant_data


if __name__ == '__main__':
    base_dir = r'/home/eiraola/data/data_tritium/02.complete_dyn_set/'
    if not os.path.isdir(base_dir):
        base_dir = (r'/media/eiraola/Elements/data/data_te/'
                    r'00.complete_dyn_set/SS-dyn')

    assert os.path.isdir(base_dir)
    plant_dir = os.path.join(base_dir, 'original/SS-dyn', 'plant')
    model_dir = os.path.join(base_dir, 'original/SS-dyn', 'model')
    dst_dir = os.path.join(base_dir, 'SS-dyn')
    assert os.path.isdir(plant_dir)
    assert os.path.isdir(model_dir)
    assert os.path.isdir(dst_dir)
    assert os.path.isdir(os.path.join(dst_dir, 'plant'))
    assert os.path.isdir(os.path.join(dst_dir, 'model'))
    assert os.path.isdir(os.path.join(dst_dir, 'residuals'))

    # Process reference plant files
    ref_plant_noc_file_short = \
        (r'/home/eiraola/data/data_tritium/02.complete_dyn_set/original/'
         r'SS-dyn/plant/plant_short_idv0_0000.csv')
    ref_plant_noc_file_long = \
        (r'/home/eiraola/data/data_tritium/02.complete_dyn_set/original/'
         r'SS-dyn/plant/plant_long_idv0_0000.csv')
    ref_plant_data_short = preprocess_plant_data(ref_plant_noc_file_short)
    ref_plant_data_long = preprocess_plant_data(ref_plant_noc_file_long)

    for case_type in ("short", "long"):
        loop_plant_model_data(case_type)
