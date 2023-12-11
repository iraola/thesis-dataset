"""
Do data split (check readme)
"""
import math
import os
import pandas as pd
from MLdetect.utils import check_esd
import shutil

# Important parameters
pulse_type = 'long'
noc_len = 10
n_consecutive = 2
n_noc = {'train': 7,
         'train-dev': 8,
         'val': 9,
         'test': 10}

# Directory init
base_dir = '/home/eiraola/data/data_tritium/'
src_dir = os.path.join(base_dir, '02.complete_dyn_set/SS-dyn')
src_dir_plant = os.path.join(src_dir, 'plant')
src_dir_res = os.path.join(src_dir, 'residuals')
# dst_dir = '.'
dst_dir = '.'
assert os.path.isdir(src_dir_res)
assert os.path.isdir(src_dir_plant)
assert os.path.isdir(dst_dir)
idv_path = 'teidv.csv'

# Get NOC files for train and train-dev
plant_noc_filelist = [os.path.join(src_dir_plant, file)
                      for file in os.listdir(src_dir_plant)
                      if 'idv0_' in file and pulse_type in file]
res_noc_filelist = [os.path.join(src_dir_res, file)
                    for file in os.listdir(src_dir_res)
                    if 'idv0_' in file and pulse_type in file]
assert len(plant_noc_filelist) == noc_len

do_dataset = {}
for dataset in n_noc.keys():
    # Make dirs if not existing
    if not os.path.isdir(os.path.join(dst_dir, dataset)):
        os.mkdir(os.path.join(dst_dir, dataset))
    # True if folder is empty
    do_dataset[dataset] = len(os.listdir(os.path.join(dst_dir, dataset))) == 0

# Start distribution loop
i = 1
i_dataset = 0
datasets = list(n_noc.keys())
# Do residual files based on plant ones (sibling cases) by pairs
for plant_filepath in plant_noc_filelist:
    # Get paths
    plant_filename = plant_filepath.split(os.sep)[-1]
    case_name = '_'.join(plant_filename.split('_')[1:])
    res_filename = f'res_{case_name}'
    res_filepath = os.path.join(src_dir_res, res_filename)
    assert os.path.isfile(res_filepath), f"File {res_filepath} doesn't exist"
    dataset = datasets[i_dataset]
    dst_path = os.path.join(dst_dir, dataset)
    if do_dataset[dataset]:
        print(f'Copying file {plant_filepath.split(os.sep)[-1]} to {dataset}')
        shutil.copy2(plant_filepath, dst_path)
        shutil.copy2(res_filepath, dst_path)
    else:
        print(f'WARNING: Files already exist in destination directory '
              f'{dataset}. Skipping directory!')
    i += 1
    if i > n_noc[dataset]:
        i_dataset += 1

# Handle fault files for val and test sets
plant_fault_filelist = [
    os.path.join(src_dir_plant, file) for file in os.listdir(src_dir_plant)
    if 'idv0_' not in file and pulse_type in file]
res_fault_filelist = [
    os.path.join(src_dir_res, file) for file in os.listdir(src_dir_res)
    if 'idv0_' not in file and pulse_type in file]
assert len(plant_fault_filelist) == len(res_fault_filelist), \
    f"Number of res/model fault files don't match"

idv_datasets = ['val', 'test']
i = 0
dataset = idv_datasets[0]
for plant_filepath in plant_fault_filelist:
    # Get paths
    plant_filename = plant_filepath.split(os.sep)[-1]
    case_name = '_'.join(plant_filename.split('_')[1:])
    res_filename = f'res_{case_name}'
    res_filepath = os.path.join(src_dir_res, res_filename)
    assert os.path.isfile(res_filepath), f"File {res_filepath} doesn't exist"
    # Check ESD
    df = pd.read_csv(plant_filepath)
    esd_flag, _ = check_esd(df, n_consecutive=n_consecutive)
    if esd_flag:
        print('WARNING: ESD in', plant_filepath)
    # Check if files already exist
    dst_path = os.path.join(dst_dir, dataset)
    if not os.path.isdir(dst_path):
        os.mkdir(dst_path)
    if os.path.exists(os.path.join(dst_path, plant_filename)):
        print(f'WARNING: File {plant_filename} already exists '
              f'in destination directory {dataset}. Skipping file!')
        continue
    if os.path.exists(os.path.join(dst_path, res_filename)):
        print(f'WARNING: File {res_filename} already exists '
              f'in destination directory {dataset}. Skipping file!')
        continue
    # Distribute files
    print(f'Copying file {plant_filename} and {res_filename} to {dataset}')
    shutil.copy2(plant_filepath, dst_path)
    shutil.copy2(res_filepath, dst_path)
    i += 1
    if i == math.ceil(len(plant_fault_filelist) / 2):
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
