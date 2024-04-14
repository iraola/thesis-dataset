"""
Emulate model data by simplifying a run of plant scenario.

Use a moving average filter to smooth the data and add an offset to each
column. The offset is a random number with mean 5 % and with a 50 % probability
of being above or below (sum or subtract), doing both things for each column.
"""
import json
import os

import matplotlib.pyplot as plt
import scienceplots
import numpy as np
import pandas as pd

from data_prep import preprocess_plant_data

plt.style.use('science')


def average_cycles(df):
    # Check if the dataframe has at least 9 cycles
    if len(df) < 450:
        raise ValueError("Dataframe must have at least 500 rows")

    # Initialize an empty dataframe to store averaged cycles
    averaged_df = pd.DataFrame()

    # Iterate over time steps (columns)
    for timestep in range(50):
        # Slice the dataframe for each timestep in cycles 3 to 9
        # Start from cycle 3 to cycle 9, skipping 50 rows for each cycle
        timestep_df = df.iloc[100 + timestep::50]
        # Calculate the mean for each column across cycles
        timestep_mean = timestep_df.mean(axis=0)
        # Append the averaged timestep to the dataframe
        averaged_df = pd.concat([averaged_df, timestep_mean], axis=1)
    averaged_df = averaged_df.T.reset_index(drop=True)  # Transpose and reset index

    # Repeat the averaged cycle to match the original dataframe size
    repeated_averaged_df = pd.concat([averaged_df] * 10, ignore_index=True)

    # Set index to match required sampling times
    repeated_averaged_df.index = \
        repeated_averaged_df.index * sample_time_seconds + sample_time_seconds

    return repeated_averaged_df


# Process reference plant files
base_dir = '/home/eiraola/data/data_tritium/02.complete_dyn_set/original/'
# The 0005 file has originally perfect cycles (all are of 50 instances exactly
#  while others are not)
ref_plant_noc_file_short = os.path.join(
    base_dir, 'SS-dyn/plant/plant_short_idv0_0005.csv')
dst_dir = os.path.join(base_dir, 'SS-dyn/simple_model')
image_dir = os.path.join('/home/eiraola/projects/tep2py/images',
                         'tep_simple_model')
if not os.path.isdir(dst_dir):
    os.makedirs(dst_dir)
if not os.path.isdir(image_dir):
    os.makedirs(image_dir)

# Get dataset parameters from setup.json
with open('setup.json', 'r') as f:
    setup = json.load(f)
    sample_time_seconds = int(setup['sample_time_seconds'])

# Smoothing parameters
window_size = 10

sc_len = (100, 200)
rng = np.random.default_rng(42)

flag_short = True
for ref_file in [ref_plant_noc_file_short]:
    assert os.path.isfile(ref_file)
    # Preprocess before filtering since it won't trim the same later on.
    ref_df = preprocess_plant_data(ref_file)
    total_inv = ref_df['XINT(11)']
    # Average cycles
    averaged_df = average_cycles(ref_df)
    # Filter data
    model_df = averaged_df.rolling(
        window=window_size, center=True, min_periods=1).mean()
    # Recover all SP columns so that they are not affected by the filter
    for col in averaged_df.columns:
        if 'SP' in col:
            model_df[col] = averaged_df[col]

    # Add an offset with mean 5 % and with a 50 % probability of being above
    #  or below (sum or subtract), doing both things for each column
    for i, col in enumerate(model_df.columns):
        if 'IDV' in col or 'SP' in col:
            continue

        # Modify data
        if (col == 'XINT(8)' or col == 'XINT(9)' or col == 'XINT(10)' or
                col == 'XINT(11)'):
            # Special case for XINT(11) since it is the total inventory
            #  - Do not do filtering
            #  - Use the averaged cycle for all cycles
            model_df[col] = averaged_df[col]
            inv_dev = np.abs(model_df[col] - ref_df[col]) / 0.82 * 100
            print(f'{col} deviation: {inv_dev.mean():.2f} %')
        else:
            offset = model_df[col].mean() * 0.05
            model_df[col] += rng.choice([-1, 1]) * offset

        # Visualize
        x = ((averaged_df.index[sc_len[0]:sc_len[1]] - averaged_df.index[sc_len[0]])
             / 3600)  # hours
        if ((col == 'XMEAS(1)' or col == 'XMEAS(22)' or col == 'XINT(11)')
                and flag_short):
            plt.figure(figsize=(8, 4.8))
            if col == 'XINT(11)':
                plt.plot(x, total_inv.iloc[sc_len[0]:sc_len[1]],)
            else:
                plt.plot(x, averaged_df[col].iloc[sc_len[0]:sc_len[1]],
                         label='Plant data')
            plt.plot(x, model_df[col].iloc[sc_len[0]:sc_len[1]],
                     label='Model data')
            plt.legend()
            plt.xlabel('Time (h)')
            if col == 'XMEAS(22)':
                plt.ylabel('Temperature (°C)')
            else:
                plt.ylabel('Values')
            plt.savefig(os.path.join(
                image_dir, f'tep_simple_model_comparison_{col}.pdf'),
                        bbox_inches='tight')
            plt.title(f'Original vs Smoothed Time Series Data - {col}')
            plt.show()

    if len(averaged_df) != len(model_df):
        raise ValueError('Lengths do not match')

    flag_short = False

    # Save
    filename = os.path.basename(ref_file)
    filename = filename.replace('plant', 'model')
    model_df.to_csv(os.path.join(dst_dir, filename), index_label='Time')

    # Report XINT(11) error
    y_true = ref_df['XINT(11)']
    y_pred = model_df['XINT(11)']
    mae = np.mean(np.abs(y_true - y_pred)) / 0.82 * 100
    print(f'Mean absolute error for ref file {ref_file}: {mae:.2f} %')

