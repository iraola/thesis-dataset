"""
Generate RESIDUAL files (Fortran+HYSYS) from dynamic data (00.complete_dyn_set)
and distribute into train, train-dev, val and test sets. Also copy plant files
with the 'plant_' case identifier

Plant files:
    - NOC: 100
    - fault: 100 per fault (2000 total, since we do not have IDV(15))

Distribution:
    - train:        90 NOC cases
    - train-dev:    8 NOC cases
    - val:          1 NOC case, 50 fault cases/fault  (950 fault cases total)
    - test:         1 NOC case, 50 fault cases/fault  (950 fault cases total)

Note that for the MODEL, we only have 9 cases in total, so we will repeat them
to generate the whole RESIDUAL dataset.

Also place the original RAW (plant) files into a separate folder with the same
structure in terms of datasets.
"""

import os
import pandas as pd
from MLdetect.utils import check_esd
import shutil

# Directory init
src_dir = '/media/eiraola/Elements/data/data_te/00.complete_dyn_set/SS-dyn'
src_dir_plant = os.path.join(src_dir, 'plant')
src_dir_res = os.path.join(src_dir, 'residuals')
# dst_dir = '.'
dst_dir = '/media/eiraola/Elements/data/data_te/03.NOC_only_dyn'
assert os.path.isdir(src_dir_res)
assert os.path.isdir(src_dir_plant)
assert os.path.isdir(dst_dir)
idv_path = 'teidv.csv'

# Get NOC files for train and train-dev
n_noc = {
    'train': 90,
    'train-dev': 98,
    'val': 99,
    'test': 100
}
plant_noc_filelist = [os.path.join(src_dir_plant, file)
                      for file in os.listdir(src_dir_plant) if 'IDV0_' in file]
res_noc_filelist = [os.path.join(src_dir_res, file)
                    for file in os.listdir(src_dir_res) if 'IDV0_' in file]
assert len(plant_noc_filelist) == 100
do_dataset = {}
for dataset in n_noc.keys():
    # True if folder is empty
    do_dataset[dataset] = len(os.listdir(os.path.join(dst_dir, dataset))) == 0
# Start distribution loop
i = 1
i_dataset = 0
datasets = list(n_noc.keys())
for file_plant, file_res in zip(plant_noc_filelist, res_noc_filelist):
    dataset = datasets[i_dataset]
    dst_path = os.path.join(dst_dir, dataset)
    if do_dataset[dataset]:
        print(f'Copying file {file_plant.split(os.sep)[-1]} to {dataset}')
        shutil.copy2(file_plant, dst_path)
        shutil.copy2(file_res, dst_path)
    else:
        print(f'WARNING: Files already exist in desination directory {dataset}.'
              f' Skipping directory!')
    i += 1
    if i > n_noc[dataset]:
        i_dataset += 1

# Handle fault files for val and test sets
plant_fault_filelist = [
    os.path.join(src_dir_plant, file)
    for file in os.listdir(src_dir_plant) if 'IDV0_' not in file]
res_fault_filelist = [
    os.path.join(src_dir_res, file)
    for file in os.listdir(src_dir_res) if 'IDV0_' not in file]

idv_datasets = ['val', 'test']
i = 0
dataset = idv_datasets[0]
for file_plant, file_res in zip(plant_fault_filelist, res_fault_filelist):
    # Check ESD
    df = pd.read_csv(file_plant)
    esd_flag, _ = check_esd(df)
    if esd_flag:
        print('WARNING: ESD in', file_plant)
    # Check if files already exist
    dst_path = os.path.join(dst_dir, dataset)
    if os.path.exists(os.path.join(dst_path, file_plant.split(os.sep)[-1])):
        print(f'WARNING: File {file_plant.split(os.sep)[-1]} already exists '
              f'in destination directory {dataset}. Skipping file!')
        continue
    if os.path.exists(os.path.join(dst_path, file_res.split(os.sep)[-1])):
        print(f'WARNING: File {file_res.split(os.sep)[-1]} already exists '
              f'in destination directory {dataset}. Skipping file!')
        continue
    # Distribute files
    print(f'Copying file {file_plant.split(os.sep)[-1]} to {dataset}')
    shutil.copy2(file_plant, dst_path)
    shutil.copy2(file_res, dst_path)
    i += 1
    if i == len(plant_fault_filelist) / 2:
        dataset = idv_datasets[1]


# Rename plant files (no prefix, no 'res') into 'plant_' prefix
for dataset in datasets:
    for file in os.listdir(os.path.join(dst_dir, dataset)):
        if not file.startswith('res_') and not file.startswith('plant_'):
            os.rename(
                os.path.join(dst_dir, dataset, file),
                os.path.join(dst_dir, dataset, 'plant_' + file)
            )

# Sanity check: make sure there is no duplicates between test and val sets
test_dir = os.path.join(dst_dir, 'test')
val_dir = os.path.join(dst_dir, 'val')
for file in os.listdir(test_dir):
    if file in os.listdir(val_dir):
        print('WARNING: REPEATED FILE', file)
