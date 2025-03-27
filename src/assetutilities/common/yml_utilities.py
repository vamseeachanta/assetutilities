# Standard library imports
import importlib.util
#import logging
import os
import re
import pkgutil
import types
from collections.abc import Mapping
from pathlib import Path

# Third party imports
import yaml
from deepdiff import DeepDiff

from loguru import logger

# Reader imports
from assetutilities.common.data import ReadData
from assetutilities.common.saveData import saveDataYaml
from assetutilities.common.utilities import (
    get_common_name_from_2_filenames,
    is_file_valid_func,
)
from assetutilities.common.visualization.visualization_templates import (
    VisualizationTemplates,
)
#from assetutilities.engine import engine as aus_engine

viz_templates = VisualizationTemplates()

read_data = ReadData()


def represent_none(self, _):
    return self.represent_scalar("tag:yaml.org,2002:null", "~")


yaml.add_representer(type(None), represent_none)


def ymlInput(defaultYml, updateYml=None):

    return WorkingWithYAML().ymlInput(defaultYml, updateYml)


def update_deep(d, u):

    return WorkingWithYAML().update_deep(d, u)



class WorkingWithYAML:

    def __init__(self):
        pass

    def router(self, cfg):
        if 'yml_analysis' in cfg and cfg['yml_analysis']['divide']['flag']:
            self.divide_yaml_files(cfg)
        elif 'plot_yml_arrays' in cfg and cfg['plot_yml_arrays']['flag']:
            self.get_plot_yml(cfg)

        return cfg
    
    def get_plot_yml(self, cfg):

        yml_files = cfg['file_management']['input_files']['yml']
        for yml_file in yml_files:
            self.plot_from_yml_arrays(yml_file, cfg)

    def plot_from_yml_arrays(self, yml_file, cfg):

        with open(yml_file, "r") as ymlfile:
            documents = list(yaml.safe_load_all(ymlfile))
        data = {}
        for doc in documents:
            if isinstance(doc, dict):
                data.update(doc)
        arrays = [v for v in data.values() if isinstance(v, list) and all(isinstance(i, (int, float)) for i in v)]
    
        if len(arrays) < 2:
            raise ValueError("YAML file must contain at least two numeric arrays for plotting.")
        
        plot_yml = viz_templates.get_xy_line_input(cfg['Analysis'].copy())
        settings = {'file_name': yml_file.name,
                    'title': 'Line Plot',
                    'xlabel': 'PeriodOrFrequency',
                    'ylabel': 'WaveHeading',
                    }
        plot_yml['settings'].update(settings)
        plot_yml['data']["groups"][0]["x"] = arrays[0]
        plot_yml['data']["groups"][0]["y"] = arrays[1]
        from assetutilities.engine import engine as aus_engine
        aus_engine(inputfile=None, cfg=plot_yml, config_flag=False)
        
    def ymlInput(self, defaultYml, updateYml=None):
        if not is_file_valid_func(defaultYml):
            raise Exception("Not valid file. Please check the file path.")

        with open(defaultYml, "r") as ymlfile:
            try:
                cfg = yaml.safe_load(ymlfile)
            except yaml.composer.ComposerError:
                cfg = self.yml_read_stream(defaultYml)

        if updateYml != None:
            #  Update values file
            try:
                with open(updateYml, "r") as ymlfile:
                    cfgUpdateValues = yaml.safe_load(ymlfile)
                #  Convert to logs
                # logger.info(cfgUpdateValues)
                cfg = update_deep(cfg, cfgUpdateValues)
            except:
                logger.info(
                    "Update Input file could not be loaded successfully. Running program default values"
                )

        return cfg
        
    def yml_read_stream(self, yaml_file_name):
        stream_dict = {}
        try:
            with open(yaml_file_name, "r") as ymlfile:
                yaml_content = ymlfile.read()
            
                # Clean the YAML content
                cleaned_yaml = self.clean_yaml_file(yaml_content)
                docs = yaml.safe_load_all(cleaned_yaml)
                if type(docs) is types.GeneratorType:
                    for doc in docs:
                        if type(doc) is dict:
                            stream_dict = update_deep(stream_dict, doc)
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")                    
        except Exception as e:
            raise Exception("Stopping Program due to some inefficient data in the YAML file")

        return stream_dict
    
    def clean_yaml_line(self,line):
        """
        Cleans a single line of YAML by removing invalid tokens or characters.
        """
        # Remove lines that are comments or contain invalid tokens
        if '%' in line:
            line = re.sub(r'(\s*[^:]+:\s*)%([^%]+)%', r'\1"\2"', line)  # Wrap %...% in quotes
        return line

    def clean_yaml_file(self,yaml_content):
        """
        Cleans the entire YAML content by removing invalid lines and tokens.
        """
        cleaned_lines = []
        for line in yaml_content.splitlines():
            cleaned_line = self.clean_yaml_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return '\n'.join(cleaned_lines)

    def update_deep(self, d, u):
        for k, v in u.items():
            # this condition handles the problem
            if not isinstance(d, Mapping):
                d = u
            elif isinstance(v, Mapping):
                r = update_deep(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]

        return d

        
    def analyze_yaml_keys(self, file_name):
        '''
        Analyze Yaml file
        '''
        file_name_content = ymlInput(file_name)
        logger.info(file_name_content.keys())

    def compare_yaml_root_keys(self, file_name1, file_name2):
        '''
        Compare 2 yaml files
        '''

        file_name1_content = ymlInput(file_name1)
        file_name2_content = ymlInput(file_name2)
        file_name1_keys = file_name1_content.keys()
        file_name2_keys = file_name2_content.keys()
        if file_name1_keys == file_name2_keys:
            logger.info("Yaml files have the same root keys")
        else:
            logger.info(f"The root keys for {file_name1}: {file_name1_keys}")
            logger.info(f"The root keys for {file_name2}: {file_name2_keys}")

    def compare_yaml_files_deepdiff(self, cfg):
        '''
        Compare 2 yaml files using DeepDiff
        '''
        file_name1 = cfg["file_name1"]
        file_name2 = cfg["file_name2"]
        file_name1_content = ymlInput(file_name1)
        file_name2_content = ymlInput(file_name2)
        file_diff = DeepDiff(file_name1_content, file_name2_content, ignore_order=True)
        if file_diff == {}:  # if there is no difference
            logger.info("Yaml files are the same")
        else:
            # get file root directory
            file_directory = os.path.dirname(file_name1)
            uniquebasename = get_common_name_from_2_filenames(
                file_name1, file_name2
            )
            self.save_diff_files(file_diff, file_directory, uniquebasename)

    def compare_yaml_file_contents_deepdiff(self, cfg):
        file_name1 = cfg["file_name1"]
        file_name2 = cfg["file_name2"]

        file_name1_content = read_data.key_chain(
            ymlInput(file_name1), *cfg["map_list"]["file_name1"]
        )
        file_name2_content = read_data.key_chain(
            ymlInput(file_name2), *cfg["map_list"]["file_name2"]
        )

        file_diff = DeepDiff(file_name1_content, file_name2_content, ignore_order=True)

        self.save_diff_files(file_diff, cfg)

    def save_diff_files(self, file_diff: dict, cfg: dict, deepdiff_save: bool = False) -> None:
        file_name1 = cfg["file_name1"]
        file_name2 = cfg["file_name2"]
        if file_diff == {}:  # if there is no difference
            logger.info("Yaml files are the same")
        else:
            # get file root directory
            file_directory = os.path.dirname(file_name1)
            uniquebasename = get_common_name_from_2_filenames(file_name1, file_name2)

            # save the entire diff file. A very messy and overwhelming file
            if deepdiff_save:
                saveDataYaml(
                    file_diff, f"{file_directory}/wwyaml_{uniquebasename}_deepdiff"
                )

            file_name = f"{file_directory}/wwyaml_{uniquebasename}_updated_values.yml"
            with open(file_name, "w") as f:
                for key, value in file_diff.items():
                    if key == "values_changed":
                        for k, v in value.items():
                            f.write(f"{k}: {v['new_value']}\n")

            saveDataYaml(
                dict(file_diff), f"{file_directory}/wwyaml_{uniquebasename}_items"
            )

            saveDataYaml(
                dict(file_diff)["values_changed"],
                f"{file_directory}/wwyaml_{uniquebasename}_values_changed",
            )

            logger.info(
                "Yaml files are different. See wwyaml files saved in the current file directory"
            )

    def get_library_yaml_file(self, cfg):
        library_yaml_filename = cfg["filename"]
        library_name = cfg["library_name"]
        if os.path.isfile(library_yaml_filename):
            with open(library_yaml_filename, "r") as ymlfile:
                library_yaml = yaml.load(ymlfile, Loader=yaml.Loader)
        else:
            data = pkgutil.get_data(library_name, cfg["filename"])
            library_yaml = yaml.safe_load(data)

        return library_yaml

    def get_library_filename(self, cfg):

        filename_with_lib_path = cfg["filename"]
        library_name = cfg["library_name"]
        if not os.path.isfile(cfg["filename"]):
            lib_spec = importlib.util.find_spec(library_name)
            lib_path = Path(lib_spec.origin).parent
            filename_with_lib_path = os.path.join(lib_path, cfg["filename"])
            if not os.path.isfile(filename_with_lib_path):
                raise FileNotFoundError()

        return filename_with_lib_path


    def get_library_filepath(self, cfg, src_relative_location_flag=False):
            
            filepath_with_lib_path = cfg["filepath"]
            library_name = cfg["library_name"]
            if not os.path.isabs(filepath_with_lib_path) or not os.path.isdir(filepath_with_lib_path):
                lib_spec = importlib.util.find_spec(library_name)
                lib_path = Path(lib_spec.origin).parent
                if not src_relative_location_flag:
                    lib_path = lib_path.parents[1]
                filepath_with_lib_path = os.path.join(lib_path, cfg["filepath"])
                if not os.path.isdir(filepath_with_lib_path):
                    raise FileNotFoundError()

            return filepath_with_lib_path

    def divide_yaml_files(self, cfg) -> None:
        '''
        Iterate through yml files
        '''
        yml_files = cfg['file_management']['input_files']['yml']
        cfg[cfg['basename']] = {'divide': {'groups':[]}}
        for file_name in yml_files:
            cfg_divide = cfg['yml_analysis']['divide']
            if cfg_divide['by'] == 'primary_key':
                output_file_name_array = self.divide_yaml_file_by_primary_keys(cfg, file_name)
                cfg[cfg['basename']]['divide']['groups'].append(output_file_name_array)
            else:
                raise Exception("No divide by method specified")

    def divide_yaml_file_by_primary_keys(self, cfg, file_name) -> None:
        '''
        Divide yaml file by primary keys into individual yaml files and save them
        '''
        file_name_content = ymlInput(file_name)
    
        primary_keys = list(file_name_content.keys())

        file_name_stem = Path(file_name).stem
        result_folder = cfg['Analysis']['result_folder']

        output_file_name_array = []
        for primary_key in primary_keys:

            primary_key_clean = primary_key.encode('ascii', 'ignore').decode('ascii')
            output_file_name = f"{file_name_stem}_{primary_key_clean}.yml"
            output_file_path = os.path.join(result_folder, output_file_name)

            # Create a dictionary to add primary key to the output file 
            data_to_write = {primary_key: file_name_content[primary_key]}

            with open(output_file_path, "w") as f:
                yaml.dump(data_to_write, f, default_flow_style=False, encoding='utf-8-sig', sort_keys=False, indent=2)
                logger.info(f"{primary_key_clean}.yml has been saved in the current file directory")

            output_file_name_array.append({'data': output_file_path})
        
        return output_file_name_array

