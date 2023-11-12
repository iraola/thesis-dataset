"""
Generate residuals from dyn TE data in 00.complete_dyn_set\SS-dyn.

Note there are less model files than plant files, so they will be repeated to
generate residuals from all the plant files.
"""
import os

from pyhysys import gen_residuals

os.chdir('..')

base_dir = r'/media/eiraola/Elements/data/data_te/00.complete_dyn_set/SS-dyn'
if not os.path.isdir(base_dir):
    base_dir = r'/home/eiraola/data/data_te/00.complete_dyn_set/SS-dyn'
assert os.path.isdir(base_dir)

plant_dir = os.path.join(base_dir, 'plant')
model_dir = os.path.join(base_dir, 'model/8_cycles')
res_dir = os.path.join(base_dir, 'residuals')
assert os.path.isdir(plant_dir)
assert os.path.isdir(model_dir)
assert os.path.isdir(res_dir)

plant_file_list = [file for file in os.listdir(plant_dir)
                   if file.endswith('.csv')]
model_file_list = [file for file in os.listdir(model_dir)
                   if file.endswith('.csv')]

model_idx = 0
for plant_file in plant_file_list:
    # File and name handling
    model_filepath = os.path.join(model_dir, model_file_list[model_idx])
    assert os.path.isfile(model_filepath)
    plant_filepath = os.path.join(plant_dir, plant_file)
    assert os.path.isfile(plant_filepath)
    res_file = f'res_{plant_file}'
    res_filepath = os.path.join(res_dir, res_file)
    if os.path.isfile(res_filepath):
        print(f'File {res_filepath} already exists')
        continue
    # Call pyhysys utility function to generate residuals
    print(f'Generating residuals for {plant_file} at {res_filepath}')
    gen_residuals(plant_filepath, model_filepath, res_filepath)
    # Loop over model files
    model_idx += 1
    if model_idx >= len(model_file_list):
        model_idx = 0
