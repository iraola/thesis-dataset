"""
Fix data issues such as non-trimmed ESD cases.
"""
import json
import os
import shutil

import pandas as pd

from MLdetect.utils import check_esd


def get_case_files(data_dir, idv, n, case_type):
    """
    Return a set of one case that matches the idv argument. The returned list
    includes a file per case_id: res, plant, etc.
    """
    case_files = []
    i = 0
    for file in os.listdir(data_dir):
        if not file.endswith('.csv'):
            continue
        if f'idv{idv}_' not in file:
            continue
        if case_type not in file:
            continue
        # Get case name and find all files that match it
        case_name = '_'.join(file.strip('.csv').split('_')[1:])
        for subfile in os.listdir(data_dir):
            if case_name in subfile:
                case_files.append(subfile)
        i += 1
        if i == n:
            break
    return case_files


class DataFixer:
    def __init__(self):
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

    def relocate_siblings(self):
        """
        Move sibling cases (same case for plant and res) between 'val' and
        'test' dirs, then count number of each idv type per dir.
        """
        # Compose lists of mis-located files
        files_to_move = []
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
                        files_to_move.append(case_name)
        # Convert to set to keep unique values
        files_to_move = set(files_to_move)

        # Alternate between 'val' and 'test' dirs to end with even movements
        dirs = ['val', 'test']
        i = 1
        for case in files_to_move:
            if i % 2:
                curr_dir = dirs[0]
                other_dir = dirs[1]
            else:
                curr_dir = dirs[1]
                other_dir = dirs[0]
            # Find file that contains the case name
            for file in os.listdir(curr_dir):
                if file.endswith(self.extension) and case in file:
                    # Move file to the other dir
                    shutil.move(
                        os.path.join(curr_dir, file),
                        os.path.join(other_dir, file))
                    print(f"Moved {file} from {curr_dir} to {other_dir}")
                    break
            i += 1
        self.print_idv_proportion()

    def even_idvs(self, n_target, case_type):
        """
        Even the number of idv cases in val and test dirs.
        There should be 100 cases per idv and directory (50 res + 50 plant).
        """
        idv_dict = self.print_idv_proportion()
        dirs = ['val', 'test']
        for src_dir in dirs:
            for idv, n_cases in idv_dict[src_dir].items():
                if n_cases <= n_target:
                    continue
                # Associate directories
                if src_dir == 'val':
                    dst_dir = 'test'
                elif src_dir == 'test':
                    dst_dir = 'val'
                else:
                    raise ValueError(f"Unhandled directory {src_dir}")
                # Get number of cases to move
                n_move = (n_cases - n_target) // 2  # 2 files (res/pl) per case
                files_to_move = get_case_files(src_dir, idv, n_move, case_type)
                # Move files
                try:
                    for file in files_to_move:
                        shutil.move(
                            os.path.join(src_dir, file),
                            os.path.join(dst_dir, file))
                        print(f"Moved {file} from {src_dir} to {dst_dir}")
                except:
                    print(f"Couldn't move {file} from {src_dir} to {dst_dir},"
                          f" probably already moved")
        # Check if the number of cases is now correct
        self.print_idv_proportion()

    def print_idv_proportion(self):
        # Count number of each idv type per dir
        idv_dict = {}
        for case_id in self.case_id:
            print(f"Counting idvs for id {case_id}")
            for dir in self.dir_list:
                print(f"    Counting idvs in {dir}")
                idv_count = {}
                for file in os.listdir(dir):
                    if not file.endswith(self.extension):
                        continue
                    if not file.startswith(case_id):
                        continue
                    # Get idv from file name
                    idv = file.split('_')[2].strip('idv')
                    if idv not in idv_count:
                        idv_count[idv] = 1
                    else:
                        idv_count[idv] += 1
                for idv, num in idv_count.items():
                    print(f'        ---> idv{idv}: {num} cases')
                # Add count to general dictionary
                if dir not in idv_dict:
                    idv_dict[dir] = idv_count
                else:
                    for idv, num in idv_count.items():
                        idv_dict[dir][idv] += num
        return idv_dict

    def trim_esd_cases(self, n_consecutive=100):
        """
        Detect ESD and trim redundant data. Examine plant files only and apply
        same trim to residuals.
        """
        for dir, filelist in self.file_dict_id['plant'].items():
            if dir not in ['val', 'test']:
                continue
            for file in filelist:
                # Check plant file
                plant_filepath = os.path.join(dir, file)
                plant_df = pd.read_csv(plant_filepath)
                is_esd, esd_start = check_esd(plant_df,
                                              n_consecutive=n_consecutive)
                if not is_esd:
                    continue
                # Trim plant file
                print(f"Trimming file {plant_filepath}")
                plant_df.iloc[:esd_start, :].to_csv(plant_filepath,
                                                    index=False)
                # Check res file
                res_filepath = os.path.join(dir, f'res_{file.strip("plant_")}')
                res_df = pd.read_csv(res_filepath)
                print(f"Trimming file {res_filepath}")
                res_df.iloc[:esd_start:].to_csv(res_filepath, index=False)

    def __call__(self, *args, **kwargs):
        """ Call all class methods."""
        n_consecutive = 2
        n_idv = 10
        self.relocate_siblings()
        self.even_idvs(n_idv, case_type='short')
        self.even_idvs(n_idv, case_type='long')
        self.trim_esd_cases(n_consecutive)


if __name__ == '__main__':
    data_fixer = DataFixer()
    data_fixer()
