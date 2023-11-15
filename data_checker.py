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
        self.ignore_idvs = config['ignore_idvs']
        self.max_consecutive_times = config['max_consecutive_times']
        self.needed_files = config['needed_files']
        self.extension = config['extension']
        self.case_id = tuple(config['case_id'])
        self.esd_idvs = config['esd_idvs']

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
        numbered_vars = ['XMEAS', 'XMV', 'SP', 'XINT']
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
        numbered_vars = ['XMEAS', 'XMV', 'SP', 'XINT']
        other_vars = ['fault']
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

    def test_name_repeated(self):
        """
        Each file in each subset (train, val, ...) should not be repeated in
        other subset.
        """
        for id in self.case_id:
            for dir1 in self.dir_list:
                for file in self.file_dict_id[id][dir1]:
                    for dir2 in self.dir_list:
                        if dir1 == dir2:
                            continue
                        self.assertNotIn(
                            file, self.file_dict_id[id][dir2],
                            f'File {file} appears in both {dir1} and {dir2}')

    def test_data_len(self):
        # Assume some deviation due to necessary data trimming
        max_deviation = 5
        # Loop files in each directory
        esd_flag = False
        failed_dict = {}
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    # First discard ESD cases that will have different length
                    for idv in self.esd_idvs:
                        if f'idv{idv}_' in file:
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
                    if len(df) < self.data_len - max_deviation or \
                            len(df) > self.data_len + max_deviation:
                        failed_dict[filepath] = len(df)
        # Prints
        if len(failed_dict) > 0:
            print("Failed files:")
            for file, length in failed_dict.items():
                print(f"File {file} has length {length}")
        self.assertTrue(len(failed_dict) == 0,
                        f'Some files failed the length test.')

    def test_res_plant_homologous(self):
        """
        Check that the files in each directory are homologous. That is, that
        each plant file has a corresponding res file with similar name but
        different prefix.
        """
        if len(self.case_id) < 2:
            return
        elif len(self.case_id) > 2:
            raise ValueError('Only two case_id are supported in '
                             'test_res_plant_homologous test')
        # Loop files in each directory
        failed_dict = {}
        for ref_id in self.case_id:
            for dir in self.dir_list:
                for ref_file in self.file_dict_id[ref_id][dir]:
                    # Get next id (binary)
                    if ref_id == self.case_id[0]:
                        next_id = self.case_id[1]
                    else:
                        next_id = self.case_id[0]
                    # Get case name and next file id
                    case_name = '_'.join(ref_file.split('_')[1:])
                    next_file = f'{next_id}_{case_name}'
                    # Save the results and do the assert after processing all
                    if next_file not in self.file_dict_id[next_id][dir]:
                        failed_dict[ref_file] = dir
        self.assertTrue(len(failed_dict) == 0,
                        f'Some files failed the mutual homologous test.')
        if failed_dict:
            for ref_file, dir in failed_dict.items():
                print(f"File {ref_file} has no homologous in dir {dir}")

    def test_data_len_id_case(self):
        """
        Check that file lengths are the same for each pair "plant"-"res"
        (case_id list). ASSUME TWO CASE_ID ONLY
        """
        print()
        # Loop files in each directory
        failed_dict = {}
        ref_id = self.case_id[0]
        next_id = self.case_id[1]
        for dir in self.dir_list:
            for ref_file in self.file_dict_id[ref_id][dir]:
                # Get case name and next file id
                case_name = '_'.join(ref_file.split('_')[1:])
                next_file = f'{next_id}_{case_name}'
                # Load files and compare lengths
                ref_filepath = os.path.join(dir, ref_file)
                ref_df = pd.read_csv(ref_filepath, index_col='Time')
                next_filepath = os.path.join(dir, next_file)
                next_df = pd.read_csv(next_filepath, index_col='Time')
                # Save the results and do the assert after processing all
                if len(ref_df) != len(next_df):
                    print(f"File {ref_file} has length {len(ref_df)}, but the "
                          f"analogous file {next_file} has length "
                          f"{len(next_df)}")
                    failed_dict[ref_file] = len(ref_df)
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
        failed_dict = {}
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    if df.columns.to_list() != self.col_list:
                        print(f'File {file} in directory {dir} has wrong '
                              f'columns')
                        failed_dict[file] = len(df.columns)
        self.assertTrue(len(failed_dict) == 0,
                        f'Some files failed the test. See above for details')


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
        fault_dict = {}
        ignore_flag = False
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    # Ignore specific idvs that are known to have issues
                    for idv in self.ignore_idvs:
                        if f'idv{idv}_' in file:
                            ignore_flag = True
                    if ignore_flag:
                        ignore_flag = False
                        continue
                    # Check every column of the file
                    for col in df.columns:
                        if col in self.col_ignore_list:
                            continue
                        if df[col].diff().eq(0) \
                                .rolling(max_consecutive_times).sum() \
                                .gt(max_consecutive_times - 1).any():
                            if file in fault_dict:
                                fault_dict[file].append(col)
                            else:
                                fault_dict[file] = [col]
                    if file in fault_dict:
                        print(
                            f'File {file} in directory {dir} has more than'
                            f' {max_consecutive_times} consecutive equal'
                            f' values in columns {fault_dict[file]}')
        self.assertTrue(len(fault_dict) == 0, f'Some files failed the test.'
                                              f'See above for details')

    def test_unique_faults(self):
        """
        Check the values in the fault columns are only 0 if the filename
        contains 'idv0_', or 0 and "idv" if the file contains 'idv{idv}_'.
        """
        for id in self.case_id:
            for dir in self.dir_list:
                for file in self.file_dict_id[id][dir]:
                    filepath = os.path.join(dir, file)
                    df = pd.read_csv(filepath, index_col='Time')
                    if 'idv0_' in file:
                        self.assertEqual(df['fault'].unique(), [0])
                    else:
                        # Obtain idv from filename
                        idv = int(
                            [item for item in file.split('_')
                             if 'idv' in item][0].strip('idv')
                        )
                        for i in df['fault'].unique():
                            self.assertIn(i, [0, idv])
