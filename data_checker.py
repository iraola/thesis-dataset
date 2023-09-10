"""
data_checker.py

To check the integrity of the data in this directory
"""
import os
import json

import numpy as np
import pandas as pd

from unittest import TestCase, skip


class Test(TestCase):

    def __init__(self, methodName: str = ...):
        super().__init__(methodName)

    def setUp(self) -> None:
        # Read setup json and store information of the dataset
        setup_path = 'setup.json'
        with open(setup_path) as f:
            config = json.load(f)
        self.name = config['name']
        self.data_len = config['length']
        self.n_files = config['subsets']
        self.dir_list = list(config['subsets'].keys())
        self.vars = config['vars']
        self.has_clean_xmeas = config['has_clean_xmeas']
        self.xmeas_composition_dict = config['xmeas_composition']
        self.ignore_vars = config['ignore']
        self.ignore_files = config['ignore_files']
        self.max_consecutive_times = config['max_consecutive_times']
        self.needed_files = config['needed_files']
        self.extension = config['extension']
        self.case_id = tuple(config['case_id'])
        self.esd_idv = config['esd_idv']

        # Create file dictionary
        file_dict_id = {}
        for id in self.case_id:
            file_dict = dict.fromkeys(self.dir_list, [])
            for dir in self.dir_list:
                file_dict[dir] = [
                    file for file in os.listdir(dir)
                    if file.endswith(self.extension) and file.startswith(id)]
            file_dict_id[id] = file_dict
        self.file_dict_id = file_dict_id

        # Generate list of columns
        self.col_list = self.gererate_col_list()
        self.col_comp_list = self.generate_col_list_composition()
        self.col_ignore_list = self.generate_col_list_ignore()

    def gererate_col_list(self):
        col_list = []
        numbered_vars = ['XMEAS', 'XMV', 'SP', 'FMOL']
        append_A_vars = ['UC', 'FMOL']
        for var, max in self.vars.items():
            # Main cases
            if var in numbered_vars:
                col_list += [f'{var}({i})' for i in range(1, max + 1)]
            elif var == 'UC':
                col_list += ['UCVR', 'UCLR', 'UCVS', 'UCLS', 'UCLC', 'UCVV']
            elif var == 'fault':
                # fault is skipped for the end
                continue
            else:
                raise ValueError(
                    f'Variable {var} not implemented, check setup file')

            # Loop to add special cases
            if var in append_A_vars:
                if var == 'UC':
                    col_list += ['UCVR_A', 'UCLR_A', 'UCVS_A', 'UCLS_A',
                                 'UCLC_A', 'UCVV_A']
                else:
                    col_list += [f'{var}({i})_A' for i in range(1, max + 1)]
        # Add XMEAS()_clean vars
        if self.has_clean_xmeas and 'XMEAS' in self.vars.keys():
            # Add XMEAS()_clean vars
            max = self.vars['XMEAS']
            col_list += [f'XMEAS({i})_clean' for i in range(1, max + 1)]
        # Leave fault for the end
        if 'fault' in self.vars:
            col_list += ['fault']
        return col_list

    def generate_col_list_composition(self):
        start = self.xmeas_composition_dict['start']
        end = self.xmeas_composition_dict['end']
        indices = np.arange(start, end + 1)
        col_comp_list = [f'XMEAS({i})' for i in indices]
        if self.has_clean_xmeas:
            col_comp_list += [f'XMEAS({i})_clean' for i in indices]
        return col_comp_list

    def generate_col_list_ignore(self):
        """ Get list of columns that will be ignored. """
        col_ignore_list = []
        numbered_vars = ['XMEAS', 'XMV', 'SP']
        append_A_vars = ['UC', 'FMOL']
        other_vars = append_A_vars + ['fault']
        for var, subvars in self.ignore_vars.items():
            if var in numbered_vars:  # e.g. var is 'XMV', subvars is [1, 2]
                for i in subvars:
                    col = f'{var}({i})'
                    col_ignore_list.append(col)
            elif var in other_vars:  # e.g. var is 'UC', subvars is ['UCLR']
                for subvar in subvars:
                    col_ignore_list.append(subvar)
            else:
                raise ValueError(
                    f'Variable {var} not implemented, check setup file')
        return col_ignore_list

    def test_dir_exists(self):
        for dir in self.dir_list:
            self.assertTrue(os.path.exists(dir),
                            f'Directory {dir} does not exist')

    def test_not_empty(self):
        for dir in self.dir_list:
            self.assertTrue(len(os.listdir(dir)) > 0)

    def test_not_empty_filedict(self):
        for id in self.case_id:
            for dir in self.dir_list:
                self.assertTrue(len(self.file_dict_id[id][dir]) > 0)

    def test_n_files(self):
        for id in self.case_id:
            for dir in self.dir_list:
                id_filelist = self.file_dict_id[id][dir]
                self.assertEqual(len(id_filelist), self.n_files[dir])

    def test_needed_files(self):
        for file in self.needed_files:
            self.assertTrue(os.path.exists(file))

    def test_data_len(self):
        # Loop files in each directory
        esd_flag = False
        failed_dict = {}
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    # First discard ESD cases that will have different length
                    for idv in self.esd_idv:
                        if idv + "_" in file:
                            esd_flag = True
                            break
                    if esd_flag:
                        esd_flag = False
                        print("Skipping potential ESD case:", file)
                        continue

                    # Now load file and check length
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    # Save the results and do the assert after processing all
                    if len(df) != self.data_len:
                        failed_dict[filepath] = len(df)
        # Prints
        if len(failed_dict) > 0:
            print("Failed files:")
            for file, length in failed_dict.items():
                print(f"File {file} has length {length}")
        self.assertTrue(len(failed_dict) == 0,
                         f'Some files failed the length test.')

    def test_cols(self):
        """
        Check number of vars and check all columns are present based on
        self.vars. self.vars is a dictionary thathas the following structure:
            "XMEAS": 41,
            "XMV": 11,
            "SP": 20,
            "UC": 12,
            "FMOL": 26,
            "fault": 1
        meaning that the dataframe should contain 41 columns named "XMEAS(1),
        XMEAS(2), ..., XMEAS(41)", 11 columns named "XMV(1), XMV(2), ..., etc.
        """
        # Compare number of columns in col_list with all files
        # Verify that each column is identical to the one in col_list
        # Also check that the order is the same. Both lists should be identical
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    self.assertEqual(
                        len(df.columns), len(self.col_list),
                        f'File {file} in directory {dir} has wrong number of'
                        f' columns: {len(df.columns)} instead of '
                        f'{len(self.col_list)}. Its columns are {df.columns}')
                    self.assertEqual(
                        df.columns.to_list(), self.col_list,
                        f'File {file} in directory {dir} has wrong columns: '
                        f'{df.columns.to_list()}')

    def test_check_null_cols(self):
        """
        Check that there are no NaN/null/None values in every column except the
        ones in self.ignore_vars
        """
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    for col in df.columns:
                        if col in self.col_ignore_list:
                            continue
                        self.assertFalse(
                            df[col].isnull().values.any(),
                            f'File {file} in directory {dir} has NaN values'
                            f' in column {col}')

    def test_bugged_cols(self):
        """
        Verify that each column does not have more than 3 consecutive equal
        values except for the ones in self.ignore_vars.
        For XMEAS composition columns, only check they have more than three
        unique values overall.
        """
        max_consecutive_times = self.max_consecutive_times
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    # Ignore very specific files we checked manually
                    if file in self.ignore_files:
                        continue
                    for col in df.columns:
                        if col in self.col_ignore_list:
                            continue
                        # if col in self.col_comp_list:
                        #     self.assertTrue(
                        #         len(df[col].unique()) > max_consecutive_times,
                        #         f'File {file} in directory {dir} has has only '
                        #         f'one unique value in column {col}')
                        else:
                            self.assertFalse(
                                df[col].diff().eq(0)
                                .rolling(max_consecutive_times).sum()
                                .gt(max_consecutive_times - 1).any(),
                                f'File {file} in directory {dir} has more than'
                                f' {max_consecutive_times} consecutive equal'
                                f' values in column {col}')

    def test_unique_faults(self):
        """
        Check the values in the fault columns are only 0 if the filename
        contains 'IDV0_', or 0 and "idv" if the file contains 'IDV{idv}_'.
        """
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    if 'IDV0_' in file:
                        self.assertEqual(df['fault'].unique(), [0])
                    else:
                        # Obtain idv from filename
                        idv = int(
                            [item for item in file.split('_')
                             if 'IDV' in item][0].strip('IDV')
                        )
                        for i in df['fault'].unique():
                            self.assertIn(i, [0, idv])
