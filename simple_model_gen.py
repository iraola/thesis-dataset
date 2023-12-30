"""
Emulate model data by simplifying a run of plant scenario.

Use a moving average filter to smooth the data and add an offset to each
column. The offset is a random number with mean 5 % and with a 50 % probability
of being above or below (sum or subtract), doing both things for each column.
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_prep import preprocess_plant_data

# Process reference plant files
base_dir = '/home/eiraola/data/data_tritium/02.complete_dyn_set/original/'
ref_plant_noc_file_short = os.path.join(
    base_dir, 'SS-dyn/plant/plant_short_idv0_0001.csv')
ref_plant_noc_file_long = os.path.join(
    base_dir, 'SS-dyn/plant/plant_long_idv0_0001.csv')
dst_dir = os.path.join(base_dir, 'SS-dyn/simple_model')
if not os.path.isdir(dst_dir):
    os.makedirs(dst_dir)

# Smoothing parameters
window_size = 10
half_window = window_size // 2

sc_len = 100
rng = np.random.default_rng(42)

for ref_file in [ref_plant_noc_file_short, ref_plant_noc_file_long]:
    assert os.path.isfile(ref_file)
    # Preprocess before filtering since it won't trim the same later on.
    ref_df = preprocess_plant_data(ref_file)
    model_df = ref_df.rolling(
        window=window_size, center=True, min_periods=1).mean()

    # Add an offset with mean 5 % and with a 50 % probability of being above
    #  or below (sum or subtract), doing both things for each column
    for i, col in enumerate(model_df.columns):
        if 'XMEAS' not in col:
            continue
        offset = model_df[col].mean() * 0.05
        model_df[col] += rng.choice([-1, 1]) * offset
        # Visualize
        if i <= 33:
            plt.figure(figsize=(10, 6))
            plt.plot(ref_df[col].iloc[:sc_len], label='Original Data', color='blue')
            plt.plot(model_df[col].iloc[:sc_len], label='Smoothed Data', color='red')
            plt.legend()
            plt.title(f'Original vs Smoothed Time Series Data - {col}')
            plt.xlabel('Time')
            plt.ylabel('Values')
            plt.show()
            pass

    if len(ref_df) != len(model_df):
        raise ValueError('Lengths do not match')

    # Save
    filename = os.path.basename(ref_file)
    filename = filename.replace('plant', 'model')
    model_df.to_csv(os.path.join(dst_dir, filename), index_label='Time')
