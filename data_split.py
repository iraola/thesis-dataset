"""
Copy RESIDUAL files (Fortran+HYSYS) already generated at
data\rieth_mcavoy_36\residuals in the new `test` and `val` sets
"""

import os
import pandas as pd
from teutils import check_esd
import matplotlib.pyplot as plt
from pdb import set_trace
import random
import shutil

# Directory init
os.chdir(r'../..')
old_dir_1 = os.path.join('data', 'rieth_mcavoy_36', 'residuals', 'train')
old_dir_2 = os.path.join('data', 'rieth_mcavoy_36', 'residuals', 'test')
old_dirs = [old_dir_1, old_dir_2]
dst_dir = os.path.join('data', '01.NOC_only_residuals_SS')
idv_path = 'teidv.csv'

# Get NOC files for train and train-dev
n_train = 92
n_train_dev = 8
noc_filelist = []
for old_dir in old_dirs:
    noc_filelist += [os.path.join(old_dir, file) for
                     file in os.listdir(old_dir) if 'IDV0_' in file]
assert len(noc_filelist) == n_train + n_train_dev
# Distribute files
assert len(os.listdir(os.path.join(dst_dir, 'train'))) == 0, (
    'Directory needs to be empty'
)
assert len(os.listdir(os.path.join(dst_dir, 'train-dev'))) == 0, (
    'Directory needs to be empty'
)
for i in range(len(noc_filelist)):
    if i < n_train:
        dst_path = os.path.join(dst_dir, 'train')
    else:
        dst_path = os.path.join(dst_dir, 'train-dev')
    shutil.copy2(noc_filelist[i], dst_path)


# Get number of included IDVs (INCLUDE IDV13 SINCE IS NOC-only CASES)
n_val_test = 2  # Do all faults twice
idv_df = pd.read_csv(idv_path, index_col='IDV')
n_idv = len(idv_df)  # Number of disturbances (excluded or not)
used_idv_df = idv_df[idv_df['Excluded'] == 0]
used_idv = used_idv_df.index.to_list() + [0] + [13]
# Get fault files for val and test sets
fault_filelist = []
for old_dir in old_dirs:
    fault_filelist += [os.path.join(old_dir, file) for
                       file in os.listdir(old_dir) if 'IDV0_' not in file]
# Distribute files
assert len(os.listdir(os.path.join(dst_dir, 'val'))) == 0, (
    'Directory needs to be empty'
)
assert len(os.listdir(os.path.join(dst_dir, 'test'))) == 0, (
    'Directory needs to be empty'
)
for dataset in ['val', 'test']:
    for idv in used_idv * n_val_test:
        for filepath in fault_filelist:
            if f'IDV{idv}_' in filepath:
                dst_path = os.path.join(dst_dir, dataset)
                fault_filelist.remove(filepath)
                shutil.copy2(filepath, dst_path)
                break


# Sanity check: make sure there is no duplicates between test and val sets
test_dir = os.path.join(dst_dir, 'test')
val_dir = os.path.join(dst_dir, 'val')
for file in os.listdir(test_dir):
    if file in os.listdir(val_dir):
        print('WARNING: REPEATED FILE', file)
