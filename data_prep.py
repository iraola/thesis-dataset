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
        case_name = '_'.join(plant_file.split('_')[1:])
        res_file = f'res_{case_name}'
        res_filepath = os.path.join(res_dst_dir, res_file)
        plant_dst_filepath = os.path.join(plant_dst_dir, plant_file)
        if os.path.isfile(res_filepath) and os.path.isfile(plant_dst_filepath):
            print(
                f'File {res_filepath} and {plant_dst_filepath} already exist')
            continue
        # Call plant/residual preprocessor
        preprocess_data_tep(plant_filepath, model_filepath, res_filepath,
                            plant_dst_filepath=plant_dst_filepath)
        # Loop over model files
        model_idx += 1
        if model_idx >= len(model_file_list):
            model_idx = 0


def preprocess_data_tep(plant_filepath, model_filepath, res_dst_filepath,
                        plant_dst_filepath=None):
    """
    Calculate residuals from single case plant and model data. Expects one-hot
    encoded labels.
    For the TEP case, align simulation timestamping based on SP(1).
    Save to files:
        - plant file
        - residual file
    """
    expected_n_cols = 228

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
        sp1 = df['SP(1)']
        n_consecutive = 0
        for i in range(len(sp1)):
            if np.isclose(sp1.iloc[i], sps[0]):
                n_consecutive += 1
            else:
                break
        df.drop(df.index[:n_consecutive], inplace=True)

    # Accumulate XMEAS(3) to XMEAS(9) since the model only has one
    perm_cols = [f'XMEAS({i})' for i in range(3, 10)]
    perm_clean_cols = [f'XMEAS({i})_clean' for i in range(3, 10)]
    nan_cols = [f'XMEAS({i})' for i in range(4, 10)] \
        + [f'XMEAS({i})_clean' for i in range(4, 10)]
    plant_data['XMEAS(3)'] = plant_data[perm_cols].sum(axis=1)
    plant_data['XMEAS(3)_clean'] = plant_data[perm_clean_cols].sum(axis=1)
    plant_data[nan_cols] = np.nan

    # Generate residuals
    res_data, labels = gen_residuals(model_data, plant_data)

    # Write plant and residuals
    res_data.to_csv(res_dst_filepath)
    if plant_dst_filepath is not None:
        plant_data.to_csv(plant_dst_filepath)


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


if __name__ == '__main__':
    base_dir = r'/home/eiraola/data/data_tritium/02.complete_dyn_set/'
    if not os.path.isdir(base_dir):
        base_dir = (r'/media/eiraola/Elements/data/data_te/'
                    r'00.complete_dyn_set/SS-dyn')

    assert os.path.isdir(base_dir)
    plant_dir = os.path.join(base_dir, 'original/SS-dyn', 'plant')
    model_dir = os.path.join(base_dir, 'original/SS-dyn', 'model')
    res_dst_dir = os.path.join(base_dir, 'SS-dyn', 'residuals')
    plant_dst_dir = os.path.join(base_dir, 'SS-dyn', 'plant')
    assert os.path.isdir(plant_dir)
    assert os.path.isdir(model_dir)
    assert os.path.isdir(res_dst_dir)
    assert os.path.isdir(plant_dst_dir)

    for case_type in ("short", "long"):
        loop_plant_model_data(case_type)
