# Standard library imports
import importlib.util

# import logging
import os
import pkgutil
import types
from collections.abc import Mapping
from pathlib import Path

# Third party imports
import yaml
import yaml.composer
from deepdiff import DeepDiff
from jinja2 import Environment, StrictUndefined
from loguru import logger

# Reader imports
from assetutilities.common.data import ReadData
from assetutilities.common.saveData import saveDataYaml
from assetutilities.common.utilities import (
    get_common_name_from_2_filenames,
    is_file_valid_func,
)
from assetutilities.common.visualization.visualization_templates_matplotlib import (
    VisualizationTemplates,
)
from assetutilities.modules.yml_utilities.ruamel_yaml import RuamelYAML

# from assetutilities.engine import engine as aus_engine

viz_templates = VisualizationTemplates()

read_data = ReadData()
ruamel_yaml_utilities = RuamelYAML()


def represent_none(self, _):
    return self.represent_scalar("tag:yaml.org,2002:null", "~")


yaml.add_representer(type(None), represent_none)


def ymlInput(defaultYml, updateYml=None):
    return WorkingWithYAML().ymlInput(defaultYml, updateYml)


def update_deep(d, u):
    return WorkingWithYAML().update_deep(d, u)


class WorkingWithYAML:
    """
    yaml utilities module for handling YAML files.

    """

    def __init__(self):
        pass

    def router(self, cfg):
        if (
            "yml_analysis" in cfg
            and cfg["yml_analysis"]["divide"]["technique"] == "ruamel_yml"
        ):
            ruamel_yaml_utilities.router(cfg)
        elif "plot_yml_data" in cfg and cfg["plot_yml_data"]["flag"]:
            cfg = self.get_plotting_data(cfg)
            cfg = self.plot_yml_data(cfg)
        elif "test_variables" in cfg and cfg["test_variables"]["flag"]:
            self.test_variables(cfg)

        return cfg

    def get_plotting_data(self, cfg):
        groups_key_chain = cfg["data"]["groups_key_chain"]
        groups = groups_key_chain.copy()
        for group_idx, group in enumerate(groups_key_chain):
            for x_list_idx, x_list in enumerate(group["x"]):
                x_list_values = self.get_data_from_file_keychain(cfg, x_list)
                groups[group_idx]["x"][x_list_idx] = x_list_values
            for y_list_idx, y_list in enumerate(group["y"]):
                y_list_values = self.get_data_from_file_keychain(cfg, y_list)
                groups[group_idx]["y"][y_list_idx] = y_list_values

        cfg["data"]["groups"] = groups.copy()

        return cfg

    def get_data_from_file_keychain(self, cfg, file_keychain):
        file_name = file_keychain["file_name"]
        key_chain = file_keychain["key_chain"]

        if not os.path.isfile(file_name):
            file_name = os.path.join(cfg["Analysis"]["analysis_root_folder"], file_name)
            if not os.path.isfile(file_name):
                raise FileNotFoundError(f"File {file_name} does not exist.")

        # file_name_dict = self.ymlInput(file_name)
        # cleaned_yaml, ruamel_data_dict = ruamel_yaml_utilities.load_clean_yaml_file(file_name)
        # safe_yaml = YAML(typ='safe')
        # ruamel_data_dict = safe_yaml.load(cleaned_yaml)

        data = self.load_yml_with_utf_8_sig(file_name)

        for key in key_chain:
            data = data[key].copy() if isinstance(data, dict) else data[int(key)]

        return data

    def plot_yml_data(self, cfg):
        from assetutilities.engine import engine as au_engine

        plot_yml = viz_templates.get_xy_line_input(cfg["Analysis"].copy())
        plot_yml["settings"].update(cfg["settings"].copy())

        file_name = os.path.join(
            cfg["Analysis"]["result_plot_folder"], cfg["Analysis"]["file_name"]
        )
        plot_yml["settings"]["file_name"] = file_name

        plot_yml["data"] = cfg["data"].copy()

        au_engine(inputfile=None, cfg=plot_yml, config_flag=False)
        return cfg

    def ymlInput(self, defaultYml, updateYml=None):
        if not is_file_valid_func(defaultYml):
            raise Exception("Not valid file. Please check the file path.")

        with open(defaultYml, encoding="utf-8") as ymlfile:
            try:
                cfg = yaml.safe_load(ymlfile)
            except yaml.composer.ComposerError as e:
                logger.error(f"YAML parsing error: {e}")
                cfg = self.yml_read_stream(defaultYml)

        if updateYml is not None:
            #  Update values file
            try:
                with open(updateYml) as ymlfile:
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
            with open(yaml_file_name) as ymlfile:
                yaml_content = ymlfile.read()

                # Clean the YAML content
                # cleaned_yaml = self.clean_yaml_file(yaml_content)
                docs = yaml.safe_load_all(yaml_content)
                if type(docs) is types.GeneratorType:
                    for doc in docs:
                        if type(doc) is dict:
                            stream_dict = update_deep(stream_dict, doc)
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
        except Exception:
            raise Exception(
                "Stopping Program due to some inefficient data in the YAML file"
            )

        return stream_dict

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

    def load_yml_with_utf_8_sig(self, file_name):
        doc = yaml.safe_load(open(file_name, encoding="utf-8-sig"))

        return doc

    def analyze_yaml_keys(self, file_name):
        """
        Analyze Yaml file
        """
        file_name_content = ymlInput(file_name)
        logger.info(file_name_content.keys())

    def compare_yaml_root_keys(self, file_name1, file_name2):
        """
        Compare 2 yaml files
        """

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
        """
        Compare 2 yaml files using DeepDiff
        """
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
            uniquebasename = get_common_name_from_2_filenames(file_name1, file_name2)
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

    def save_diff_files(
        self, file_diff: dict, cfg: dict, deepdiff_save: bool = False
    ) -> None:
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
            with open(library_yaml_filename) as ymlfile:
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
        if not os.path.isabs(filepath_with_lib_path) or not os.path.isdir(
            filepath_with_lib_path
        ):
            lib_spec = importlib.util.find_spec(library_name)
            lib_path = Path(lib_spec.origin).parent
            if not src_relative_location_flag:
                lib_path = lib_path.parents[1]
            filepath_with_lib_path = os.path.join(lib_path, cfg["filepath"])
            if not os.path.isdir(filepath_with_lib_path):
                raise FileNotFoundError()

        return filepath_with_lib_path

    def test_variables(self, cfg):
        if cfg["test_variables"]["method"] == "single":
            flag, label = self.test_single_variable(cfg)
        elif cfg["test_variables"]["method"] == "directive_block":
            flag, label = self.test_directive_block(cfg)
        elif cfg["test_variables"]["method"] == "placeholder":
            flag, label = self.test_variable_placeholder(cfg)

        return cfg

    def test_single_variable(self, cfg):
        try:
            label = cfg["data"]["groups"][0]["label"]
            print("Label is reusable:", label)
            return True, label
        except KeyError as e:
            logger.error("Label cannot be accesible:", e)
            return False, None

    def test_directive_block(self, cfg):
        try:
            target_block = cfg["data"]["groups"][0]["target"]
            target_block["template"]
            logger.debug("block and it's nested value reusable:")
            return True, target_block
        except KeyError as e:
            logger.error("Directive block not accessible:", e)
            return False, None

    def test_variable_placeholder(self, cfg):
        cfg = self.process_placeholders(cfg, cfg)
        try:
            method = cfg["placeholder_tests"]["method"]
            print("yml key placeholder is reusable:", method)
            return True, method
        except KeyError as e:
            logger.error("yml key cannot be accesible:", e)
            return False, None

    def process_placeholders(self, data, context):
        """
        Recursively resolve all string fields using Jinja2 templates.
        """
        env = Environment(undefined=StrictUndefined)

        if isinstance(data, str):
            try:
                return env.from_string(data).render(**context)
            except Exception as e:
                logger.warning("Template failed: %s", e)
                return data
        elif isinstance(data, dict):
            return {k: self.process_placeholders(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.process_placeholders(i, context) for i in data]
        return data
