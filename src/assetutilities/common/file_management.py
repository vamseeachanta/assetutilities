import os
import glob
import pathlib

from assetutilities.common.utilities import is_file_valid_func
from assetutilities.common.utilities import is_dir_valid_func

import logging


class FileManagement:

    def __init__(self) -> None:
        pass

    def router(self, cfg):
        if "file_management" in cfg and cfg.file_management["flag"]:
            process_flag = True
        else:
            process_flag = False

        if process_flag:
            cfg = self.get_files_in_directory(cfg)

        return cfg

    def get_files_in_directory(self, cfg):
        file_management_input_directory = self.get_file_management_input_directory(cfg)
        file_management_output_directory = self.get_file_management_output_directory(cfg)

        cfg["Analysis"].update(
            {"file_management_input_directory": file_management_input_directory}
        )
        cfg["Analysis"].update(
            {"file_management_output_directory": file_management_output_directory}
        )

        filename_cfg = cfg.file_management["filename"].copy()

        file_extensions = cfg.file_management["filename"].get("extension", [])
        input_files = {}

        for file_ext in file_extensions:

            filename_pattern = filename_cfg.get("pattern", None)
            if filename_pattern is None:
                glob_search = f"*.{file_ext}"
            else:
                glob_search = f"*{filename_pattern}*.{file_ext}"

            raw_input_files_for_ext = list(
                file_management_input_directory.glob(glob_search)
            )

            filtered_files = raw_input_files_for_ext.copy()
            if "filters" in filename_cfg:
                cfg_filter = filename_cfg["filters"]
                filtered_files = self.get_filtered_files(raw_input_files_for_ext, cfg_filter)

            input_files.update({file_ext: filtered_files})

        cfg.file_management.update({"input_files": input_files})

        return cfg

    def get_filtered_files(self, files, cfg_filter):
        #TODO Test for multiple filter values
        # Only singleton array for cfg_filter['contains'] and cfg_filter['not_contains'] tested
        filtered_files = files.copy()
        for file in files:
            file_stem = pathlib.Path(file).stem
            filter_flag = False
            
            for cfg_filter_contains_item in cfg_filter['contains']:
                if not cfg_filter_contains_item in file_stem:
                    filter_flag = True

            for cfg_filter_not_contains_item in cfg_filter['not_contains']:
                if cfg_filter_not_contains_item in file_stem:
                    filter_flag = True

            if filter_flag:
                filtered_files.remove(file)

        return filtered_files

    def get_basenames(self, files):
        basenames = []
        for file in files:
            basenames.append(os.path.basename(file))
        return basenames

    def get_filename_without_extension(self, filename):

        basename = os.path.splitext(os.path.basename(filename))[0]
        filename_path = pathlib.Path(filename).parent
        filename_with_path = os.path.join(filename_path, basename)

        filename_without_extension = {
            "without_path": basename,
            "with_path": filename_with_path,
        }

        return filename_without_extension

    def get_file_management_input_directory(self, cfg):

        file_management_input_directory = cfg.file_management["input_directory"]
        if file_management_input_directory is None:
            file_management_input_directory = cfg.Analysis["analysis_root_folder"]

        analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
        dir_is_valid, file_management_input_directory = is_dir_valid_func(
            file_management_input_directory, analysis_root_folder
        )

        if not dir_is_valid:
            raise ValueError(
                f"Directory {file_management_input_directory} is not valid"
            )
        else:
            file_management_input_directory = pathlib.Path(
                file_management_input_directory
            )

        return file_management_input_directory

    def get_file_management_output_directory(self, cfg):

        output_directory = cfg.file_management.get("output_directory", None)

        # Use analysis root folder if output directory is not provided
        file_management_output_directory = output_directory
        dir_is_valid = False
        if file_management_output_directory is None:
            file_management_output_directory = cfg["Analysis"]['result_folder']
            dir_is_valid = True

        # Check if user-provided-directory is valid
        if not dir_is_valid:
            analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
            dir_is_valid, file_management_output_directory = is_dir_valid_func(
                file_management_output_directory, analysis_root_folder
            )

        # Create user-provided-directory if not exists
        if not dir_is_valid:
            file_management_output_directory = pathlib.Path(file_management_output_directory)
            file_management_output_directory.mkdir(parents=True, exist_ok=True)

            analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
            dir_is_valid, file_management_output_directory = is_dir_valid_func(
                file_management_output_directory, analysis_root_folder
            )

        if not dir_is_valid:
            raise ValueError(
                f"Directory {file_management_output_directory} is not valid"
            )
        else:
            file_management_output_directory = pathlib.Path(
                file_management_output_directory
            )

        return file_management_output_directory
