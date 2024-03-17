"""
Preprocess and save plant and residuals data for TEP.

- Note there are less model files than plant files, so they will be repeated to
generate residuals from all the plant files.
- It is assumed that input data has one-hot labels (columns) of the shape
IDV(0), IDV(2)... We simplify it decoding it into the traditional single
'fault' column.
- Used both for SHORT and LONG files.
"""
import json
import os
import numpy as np
import pandas as pd
from MLdetect.utils import even_dfs, one_hot_decoder


# General setup
sps = [2.837347, 7.566228]
# Read case parameters from setup.json
with open('setup.json', 'r') as f:
    setup = json.load(f)
    sample_time = int(setup['sample_time_seconds'])
    instances_in_cycle = int(setup['n_instances_cycle'])


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
        preprocess_data_tep(plant_filepath, model_filepath, dst_dir=dst_dir)
        # Loop over model files
        model_idx += 1
        if model_idx >= len(model_file_list):
            model_idx = 0


def preprocess_data_tep(plant_filepath, model_filepath, dst_dir):
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
    plant_filename = plant_filepath.split(os.sep)[-1]
    plant_dst_filepath = os.path.join(dst_dir, 'plant', f'plant_{case_name}')
    model_dst_filepath = os.path.join(dst_dir, 'model', model_filename)
    res_dst_filepath = os.path.join(dst_dir, 'residuals', f'res_{case_name}')

    # Load data
    plant_data = pd.read_csv(plant_filepath, index_col='Time')
    assert len(plant_data.columns) == expected_n_cols
    model_data = pd.read_csv(model_filepath, index_col='Time')
    assert len(model_data.columns) == expected_n_cols

    # Check starting setpoint is right for trimming in plant (model is fine)
    if not np.isclose(plant_data['SP(1)'].iloc[0], sps[0]) \
            and "idv0_0000" not in plant_filename:
        raise ValueError(
            f"SP(1) starts at unexpected value {plant_data['SP(1)'].iloc[0]}"
            f" in file {plant_filename}")
    # For both dataframes, identify the number of consecutive SP1 rows=sps[0]
    # and trim the dataframes to that length
    for df in [plant_data, model_data]:
        trim_df(df)

    # Fill to complete cycles
    plant_data = fill_to_complete_cycles(plant_data, instances_in_cycle,
                                         sample_time)

    # Check model and plant SP(1) are finally correctly aligned
    min_len = 10  # There are always misalignment with time, so ignore beyond
    if not np.allclose(plant_data['SP(1)'].iloc[:min_len],
                       model_data['SP(1)'].iloc[:min_len]):
        raise ValueError("SP(1) model and plant columns are not aligned")

    # Write model now to avoid trimming it more (only the first time)
    if not os.path.isfile(model_dst_filepath):
        model_data.to_csv(model_dst_filepath)

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


def fill_to_complete_cycles(df, n_cycle, sampling_time, ref_col='SP(19)'):
    """
    Check column SP(19). Each cycle (n_cycle) first contains a few 0's and then
    a higher quantity of 1's. If the cycle ends prematurely (i.e., the element
    i * n_cycle - x is not 1), add new rows to fill the rest remaining
    instances of the cycle.

    Args:
        df (pd.DataFrame): The dataframe to be filled.
        n_cycle (int): The number of instances in a cycle.
        sampling_time (int): The time between each row in the dataframe.
        ref_col (str): The name of the column to be checked.
    """
    # Check dataframe index and reset it (to 0, 1, ...)
    #   Later we will reconstruct it
    assert (pd.api.types.is_integer_dtype(df.index)
            or pd.api.types.is_float_dtype(df.index)), \
        "Index must be integer, not datetime or other"
    df.reset_index(drop=True, inplace=True)

    while True:
        # Find rows where the cycle changes from 1 to 0 prematurely
        potential_premature_changes = df[df[ref_col].diff() < 0].index
        len_cycles = potential_premature_changes.diff().to_list()
        len_cycles[0] = potential_premature_changes[0]
        len_cycles = [int(x) for x in len_cycles]
        # Iterate over the premature changes
        for i, index in enumerate(potential_premature_changes):
            # Calculate how many rows to insert to complete the cycle
            if len_cycles[i] == n_cycle:
                continue
            elif len_cycles[i] < n_cycle:
                rows_to_insert = n_cycle - len_cycles[i]
                # Get the last valid row with "1" as the "SP(19)" value
                last_valid_row = df.iloc[index - 1].values
                # Insert rows to complete the cycle
                for _ in range(rows_to_insert):
                    df = insert_row(df, index, last_valid_row)
                # Since the dataframe has been modified, restart the search
                break
            else:
                # If the cycle is longer than expected, remove the extra rows
                rows_to_remove = len_cycles[i] - n_cycle
                df.drop(df.index[index - rows_to_remove:index], inplace=True)
                df.reset_index(drop=True, inplace=True)
                break
        else:
            # Finish loop if all iterations went to "continue"
            break

    # Reset index to ensure consecutive row numbers
    df.reset_index(drop=True, inplace=True)

    # Reconstruct the original index
    df.index = df.index * sampling_time + sampling_time

    return df


def insert_row(df, index_to_insert, values):
    # Calculate the displacement for following rows
    sampling_time = df.index[1] - df.index[0]
    # Update the index of the existing DataFrame to accommodate the new row
    new_index = df.index.insert(index_to_insert, df.index[index_to_insert])
    # Reindex the DataFrame with the updated index
    df = df.reindex(new_index)
    # Shift indices of following rows by sampling_time units
    for i in range(index_to_insert + 1, len(df)):
        df.index.values[i] += sampling_time
    # Insert the new row into the DataFrame at the desired index
    df.iloc[index_to_insert] = values
    return df


def accumulate_perm(process_data):
    """
    Accumulate XMEAS(3) to XMEAS(9) in plant data since the model only has one.
    """
    # Accumulate permeation on XMEAS(3)
    perm_cols = [f'XMEAS({i})' for i in range(3, 10)]
    perm_clean_cols = [f'XMEAS({i})_clean' for i in range(3, 10)]
    process_data['XMEAS(3)'] = process_data[perm_cols].sum(axis=1)
    process_data['XMEAS(3)_clean'] = process_data[perm_clean_cols].sum(axis=1)
    # Set NaNs on the rest of the columns
    nan_cols = [f'XMEAS({i})' for i in range(4, 10)] \
        + [f'XMEAS({i})_clean' for i in range(4, 10)]
    process_data[nan_cols] = np.nan


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
    return plant_data


if __name__ == '__main__':
    base_dir = r'/home/eiraola/data/data_tritium/02.complete_dyn_set/'
    if not os.path.isdir(base_dir):
        base_dir = (r'/media/eiraola/Elements/data/data_te/'
                    r'00.complete_dyn_set/SS-dyn')

    assert os.path.isdir(base_dir)
    plant_dir = os.path.join(base_dir, 'original/SS-dyn', 'plant')
    model_dir = os.path.join(base_dir, 'original/SS-dyn', 'simple_model')
    dst_dir = os.path.join(base_dir, 'SS-dyn')
    assert os.path.isdir(plant_dir)
    assert os.path.isdir(model_dir)
    assert os.path.isdir(dst_dir)
    assert os.path.isdir(os.path.join(dst_dir, 'plant'))
    assert os.path.isdir(os.path.join(dst_dir, 'model'))
    assert os.path.isdir(os.path.join(dst_dir, 'residuals'))

    for case_type in ("short", "long"):
        loop_plant_model_data(case_type)
