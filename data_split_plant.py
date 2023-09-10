"""
Copy PLANT files (Fortran) already generated at
data\rieth_mcavoy_36\residuals in the new `test` and `val` sets

Only copy the files that match the names of those in
"""

import os
import pandas as pd
import shutil

# Directory init
src_dir_1 = os.path.join('..', 'rieth_mcavoy_36', 'raw', 'train')
src_dir_2 = os.path.join('..', 'rieth_mcavoy_36', 'raw', 'test')
src_dirs = [src_dir_1, src_dir_2]
dst_dirs = ['train', 'train-dev', 'val', 'test']
idv_path = 'teidv.csv'

# Get list of all plant files from source
n_train = 92
n_train_dev = 8
filedict = {}
for src_dir in src_dirs:
    for file in os.listdir(src_dir):
        if file.endswith('.csv'):
            filedict[file] = os.path.join(src_dir, file)


# Go over dst files, check equivalent filenames in src and copy them
for dst_dir in dst_dirs:
    for file in os.listdir(dst_dir):
        if file.endswith('.csv'):
            # Get case name
            case_name = file.strip('res_').strip('.csv')
            src_plant_filename = f'{case_name}.csv'
            dst_plant_filename = f'plant_{src_plant_filename}'
            # Check if file is in src
            if src_plant_filename in filedict.keys():
                dst_path = os.path.join(dst_dir, dst_plant_filename)
                # Skip if file already exists
                if os.path.exists(os.path.join(dst_path)):
                    print(
                        f'WARNING: File {file} already exists in destination')
                    continue
                # Copy file
                shutil.copy2(filedict[src_plant_filename], dst_path)
            else:
                print(f'WARNING: File {file} not found in source directory')
