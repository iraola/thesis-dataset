"""
Read csv files from the train, val, train-dev, test directories of two
different locations, trim them to fit the same length and then compare them.
Report the columns for which the data is not exactly equal. Compare only the
columns in features_detect.csv.
"""

import os
import sys
import logging

import pandas as pd


directory_old = '/media/eiraola/Elements1/data/data_tritium/03.tep_short_pulse'
directory_new = '.'

# Get features that are compared
used_features = pd.read_csv(os.path.join(directory_new, 'features_detect.csv'),
                            index_col='name')

# Read csv files
for dataset in ['train', 'val', 'train-dev', 'test']:
    dir_old = os.path.join(directory_old, dataset)
    dir_new = os.path.join(directory_new, dataset)
    for file in os.listdir(dir_new):
        if not (file.endswith('.csv') and file.startswith('plant')):
            continue
        file_old = os.path.join(dir_old, file)
        file_new = os.path.join(dir_new, file)
        assert os.path.isfile(file_old)
        assert os.path.isfile(file_new)
        print(f'Comparing {file}...')
        df_old = pd.read_csv(file_old, index_col='Time')
        df_new = pd.read_csv(file_new, index_col='Time')
        # Trim dataframes
        min_len = min(len(df_old), len(df_new))
        df_old = df_old.iloc[:min_len]
        df_new = df_new.iloc[:min_len]
        # Compare dataframes
        for col in df_new:
            if used_features.loc[col]['drop'] == 1:
                continue
            if not df_old[col].equals(df_new[col]):
                print('WARNING: Different data found')
                print(f'Column {col} is not equal in {dataset}')
                print(f'Old: {df_old[col].values}')
                print(f'New: {df_new[col].values}')
                print()
