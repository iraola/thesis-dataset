"""
Fix data issues such as non-trimmed ESD cases.
"""
import json
import os

import pandas as pd


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

    def trim_esd_data_plant(self):
        """
        Trim data from the self.ignore_files ESD causing IDVs from 'plant' files
        knowing that 'res' files are already trimmed.
        :return:
        """
        for dir, filelist in self.file_dict_id['res'].items():
            for file in filelist:
                for idv in self.esd_idvs:
                    if f'IDV{idv}_' not in file:
                        continue
                    # Get length of the res file and trim res file down to it
                    res_filepath = os.path.join(dir, file)
                    res_df = pd.read_csv(res_filepath)
                    plant_filepath = os.path.join(
                        dir, f'plant_{file.strip("res_")}')
                    plant_df = pd.read_csv(plant_filepath)
                    if len(res_df) == len(plant_df):
                        print(f"File {plant_filepath} was already trimmed")
                        continue
                    print(f"Trimming file {plant_filepath}")
                    plant_df = plant_df.iloc[:len(res_df)]
                    plant_df.to_csv(plant_filepath, index=False)

    def __call__(self, *args, **kwargs):
        self.trim_esd_data_plant()


if __name__ == '__main__':
    data_fixer = DataFixer()
    data_fixer()

