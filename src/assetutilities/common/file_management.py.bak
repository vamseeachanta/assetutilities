import os
import pathlib
from assetutilities.common.path_resolver import PathResolver

from assetutilities.common.utilities import is_dir_valid_func


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
        file_management_output_directory = self.get_file_management_output_directory(
            cfg
        )

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
                filtered_files = self.get_filtered_files(
                    raw_input_files_for_ext, cfg_filter
                )

            input_files.update({file_ext: filtered_files})

        cfg.file_management.update({"input_files": input_files})

        return cfg

    def get_filtered_files(self, files, cfg_filter):
        # TODO Test for multiple filter values
        # Only singleton array for cfg_filter['contains'] and cfg_filter['not_contains'] tested

        filtered_files = files.copy()
        for file in files:
            file_path = pathlib.Path(file)
            file_stem = file_path.stem
            conditions = []

            # Helper function for all filters to check if None or empty
            def apply_filter(filter_key):
                filter_value = cfg_filter.get(filter_key)
                return (
                    filter_value is not None
                    and filter_value != "NULL"
                    and (not isinstance(filter_value, list) or len(filter_value) > 0)
                )

            # 1. CONTAINS (must include ALL specified substrings)
            if apply_filter("contains"):
                conditions.append(
                    all(item in file_stem for item in cfg_filter["contains"])
                )

            # 2. NOT_CONTAINS (must exclude ALL specified substrings)
            if apply_filter("not_contains"):
                conditions.append(
                    all(item not in file_stem for item in cfg_filter["not_contains"])
                )

            # 3. FILE SIZE (min/max KB check)
            file_size_kb = file_path.stat().st_size / 1024  # Get size in KB

            if apply_filter("min_size_kb"):
                conditions.append(file_size_kb >= cfg_filter["min_size_kb"])

            if apply_filter("max_size_kb"):
                conditions.append(file_size_kb <= cfg_filter["max_size_kb"])

            # 4. REGEX (pattern matching)
            if apply_filter("regex"):
                import re

                try:
                    conditions.append(bool(re.search(cfg_filter["regex"], file_stem)))
                except re.error:  # Invalid regex → treat as no match
                    conditions.append(False)

            # Apply AND logic (all conditions must be True)
            if conditions and not all(conditions):
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
            file_management_output_directory = cfg["Analysis"]["result_folder"]
            dir_is_valid = True

        # Check if user-provided-directory is valid
        if not dir_is_valid:
            analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
            dir_is_valid, file_management_output_directory = is_dir_valid_func(
                file_management_output_directory, analysis_root_folder
            )

        # Create user-provided-directory if not exists
        if not dir_is_valid:
            file_management_output_directory = pathlib.Path(
                file_management_output_directory
            )
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
