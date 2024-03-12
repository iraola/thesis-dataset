"""
Emulate model data by simplifying a run of plant scenario.

Use a moving average filter to smooth the data and add an offset to each
column. The offset is a random number with mean 5 % and with a 50 % probability
of being above or below (sum or subtract), doing both things for each column.
"""
import os

import matplotlib.pyplot as plt
import scienceplots
import numpy as np
import pandas as pd

from data_prep import preprocess_plant_data

plt.style.use('science')


# Process reference plant files
base_dir = '/home/eiraola/data/data_tritium/02.complete_dyn_set/original/'
ref_plant_noc_file_short = os.path.join(
    base_dir, 'SS-dyn/plant/plant_short_idv0_0001.csv')
ref_plant_noc_file_long = os.path.join(
    base_dir, 'SS-dyn/plant/plant_long_idv0_0001.csv')
dst_dir = os.path.join(base_dir, 'SS-dyn/simple_model')
image_dir = os.path.join('/home/eiraola/projects/tep2py/images',
                         'tep_simple_model')
if not os.path.isdir(dst_dir):
    os.makedirs(dst_dir)
if not os.path.isdir(image_dir):
    os.makedirs(image_dir)

# Smoothing parameters
window_size = 10
half_window = window_size // 2

sc_len = (100, 200)
rng = np.random.default_rng(42)

flag_short = True
for ref_file in [ref_plant_noc_file_short, ref_plant_noc_file_long]:
    assert os.path.isfile(ref_file)
    # Preprocess before filtering since it won't trim the same later on.
    ref_df = preprocess_plant_data(ref_file)
    model_df = ref_df.rolling(
        window=window_size, center=True, min_periods=1).mean()

    # Add an offset with mean 5 % and with a 50 % probability of being above
    #  or below (sum or subtract), doing both things for each column
    for i, col in enumerate(model_df.columns):
        if 'IDV' in col or 'SP' in col:
            continue

        # Modify data
        if col == 'XINT(11)':
            # Special case for XINT(11) since it is the total inventory
            total_inv = model_df[col].copy()
            offset = 0.82 * 0.041  # Force approx 4.1 % deviation
            model_df[col] += rng.choice([-1, 1]) * offset
            inv_dev = np.abs(model_df[col] - total_inv) / 0.82 * 100
            print(f'XINT(11) deviation: {inv_dev.mean():.2f} %')
        else:
            offset = model_df[col].mean() * 0.05
            model_df[col] += rng.choice([-1, 1]) * offset

        # Visualize
        x = ((ref_df.index[sc_len[0]:sc_len[1]] - ref_df.index[sc_len[0]])
             / 3600)  # hours
        if ((col == 'XMEAS(1)' or col == 'XMEAS(22)' or col == 'XINT(11)')
                and flag_short):
            plt.figure(figsize=(8, 4.8))
            plt.plot(x, ref_df[col].iloc[sc_len[0]:sc_len[1]],
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

    if len(ref_df) != len(model_df):
        raise ValueError('Lengths do not match')

    flag_short = False

    # Save
    filename = os.path.basename(ref_file)
    filename = filename.replace('plant', 'model')
    model_df.to_csv(os.path.join(dst_dir, filename), index_label='Time')
