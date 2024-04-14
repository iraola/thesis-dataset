import os

import numpy as np
import pandas as pd

ref_file = 'train/plant_short_idv0_0005.csv'
model_file = ('/home/eiraola/data/data_tritium/02.complete_dyn_set/original'
              '/SS-dyn/simple_model/model_short_idv0_0005.csv')

# Load data
ref_df = pd.read_csv(ref_file, index_col='Time')
model_df = pd.read_csv(model_file, index_col='Time')

y_true = ref_df['XINT(11)']
y_pred = model_df['XINT(11)']
mae = np.mean(np.abs(y_true - y_pred)) / 0.82 * 100
print(f'Mean absolute error for ref file {ref_file}: {mae:.2f} %')

# Now do the same but over all plant files in the training set
ref_dir = 'train'
model_dir = 'model'
error_list = []
error_gram_list = []
max_error_list = []
max_error_gram_list = []
for ref_file in os.listdir(ref_dir):
    if not ref_file.startswith('plant'):
        continue
    filepath = os.path.join(ref_dir, ref_file)
    ref_df = pd.read_csv(filepath, index_col='Time')
    y_true = ref_df['XINT(11)']
    y_pred = model_df['XINT(11)']
    if len(y_pred) > len(y_true):
        y_pred = y_pred[:len(ref_df)]
    if len(y_pred) != len(y_true):
        raise ValueError('Model file different than reference file')
    errors_gram = np.abs(y_true - y_pred)
    errors = errors_gram / 0.82 * 100
    error_list.append(errors.values)
    error_gram_list.append(errors_gram.values)
    print(f'Mean absolute error for ref file {ref_file}: {errors.mean():.4f} %'
          f' (gram: {errors_gram.mean():.5f})')
    max_error_gram_list.append(errors_gram.max())
    max_error_list.append(errors.max())
    print(f'Max error for ref file {ref_file}: {errors.max():.4f} %'
          f' (gram: {errors_gram.max():.4f})')
total_errors = np.concatenate(error_list, axis=0)
total_errors_gram = np.concatenate(error_gram_list, axis=0)
total_mae = np.mean(total_errors)
total_mae_gram = np.mean(total_errors_gram)
print(f'\n\nTotal mean absolute error: {total_mae:.4f} %'
      f' (gram: {total_mae_gram:.5f})')
total_max_error = np.max(max_error_list)
total_max_error_gram = np.max(max_error_gram_list)
print(f'Total max error: {total_max_error:.4f} %'
      f' (gram: {total_max_error_gram:.4f})')
