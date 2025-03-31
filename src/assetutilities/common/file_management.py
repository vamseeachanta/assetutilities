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
            input_files.update({file_ext: raw_input_files_for_ext})

        cfg.file_management.update({"input_files": input_files})

        # else:
        #     file_extensions = cfg.file_management["input_files"].keys()
        #     for file_ext in file_extensions:
        #         raw_input_files_for_ext = cfg.file_management["input_files"][file_ext]

        #         valid_file_count = 0
        #         for input_file_index in range(0, len(raw_input_files_for_ext)):
        #             input_file = raw_input_files_for_ext[input_file_index]
        #             if not os.path.isfile(input_file):
        #                 raw_input_files_for_ext[input_file_index] = os.path.join(
        #                     cfg.Analysis["analysis_root_folder"], input_file
        #                 )
        #             if os.path.isfile(raw_input_files_for_ext[input_file_index]):
        #                 valid_file_count = valid_file_count + 1

        #         logging.info(
        #             f"Number of '{file_ext}' input files : {len(raw_input_files_for_ext)} . Valid files are: {valid_file_count}."
        #         )

        return cfg

    def get_files_in_directory_superseded(self, cfg):
        if cfg["files"]["files_in_current_directory"]["flag"]:
            file_folder = cfg["Analysis"]["analysis_root_folder"]
        else:
            file_folder = cfg["files"]["files_in_current_directory"]["directory"]

        extension = cfg["files"]["extension"]
        os.path.join(file_folder, "*." + extension)
        files = glob.glob(os.path.join(file_folder, "*." + extension))

        if "filters" in cfg["files"]:
            cfg_filter = cfg["files"]["filters"]
            filtered_files = self.get_filtered_files(files, cfg_filter)
        else:
            filtered_files = files.copy()

        basenames = self.get_basenames(filtered_files)
        cfg.update(
            {
                cfg["basename"]: {
                    "files": filtered_files,
                    "basenames": basenames,
                    "file_folder": file_folder,
                }
            }
        )

        return cfg

    def get_filtered_files(self, files, cfg_filter):
        filtered_files = files.copy()
        for file in filtered_files:
            filter_flag = False
            if (
                len(cfg_filter["filename_contains"]) > 0
                and cfg_filter["filename_contains"][0] not in file
            ):
                filter_flag = True
            if (
                len(cfg_filter["filename_not_contains"]) > 0
                and cfg_filter["filename_not_contains"][0] in file
            ):
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
        file_management_output_directory = output_directory
        if file_management_output_directory is None:
            file_management_output_directory = cfg["Analysis"]["analysis_root_folder"]

        if file_management_output_directory is not None:
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
