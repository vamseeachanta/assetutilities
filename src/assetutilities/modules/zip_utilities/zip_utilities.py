import os
from os.path import basename
from zipfile import ZipFile

from loguru import logger

# Reader imports
from assetutilities.common.utilities import is_dir_valid_func
from assetutilities.modules.zip_utilities.zip_files_to_dataframe import ZipFilestoDf

zip_files_to_df = ZipFilestoDf()


class ZipUtilities:
    def __init__(self):
        pass

    def router(self, cfg):
        if (
            cfg["analysis_settings"]["flag"]
            and cfg["analysis_settings"]["by"] == "stem"
        ):
            self.zip_files_by_stem(cfg)
        elif (
            "zip_utilities" in cfg
            and cfg["zip_utilities"]["technique"] == "zip_files_to_df"
        ):
            zip_files_to_df.router(cfg)

        return cfg

    def zip_files_by_stem(self, cfg):
        """
        Zips files in analysis_settings directory
        Uses stem name from file_management settings
        """
        file_extensions = cfg["file_management"]["filename"]["extension"]
        for file_extension in file_extensions:
            self.zip_files_by_file_extension(cfg, file_extension)

    def zip_files_by_file_extension(self, cfg, file_extension):
        stem_files_list = cfg["file_management"]["input_files"][file_extension]
        stem_list = [file.stem for file in stem_files_list]

        input_file_directory = cfg["analysis"]["input_directory"]
        analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
        test_flag, input_file_directory = is_dir_valid_func(
            input_file_directory, analysis_root_folder
        )
        input_file_extenstions = cfg["analysis"]["filename"]["extension"]
        cfg[cfg["basename"]] = []
        for stem in stem_list:
            files = []
            for file in os.listdir(input_file_directory):
                for input_file_extension in input_file_extenstions:
                    if file.__contains__(stem) and file.endswith(input_file_extension):
                        file_path = os.path.join(input_file_directory, file)
                        files.append(file_path)

            zip_file_path = self.zip_files(cfg, files, stem)
            output_dict = {"stem": stem, "zip_file_path": zip_file_path, "files": files}
            cfg[cfg["basename"]].append(output_dict)

    def zip_files(self, cfg, files, zip_stem_name):
        zip_name = f"{zip_stem_name}.zip"
        result_folder = cfg["Analysis"]["result_folder"]
        zip_file_path = os.path.join(result_folder, zip_name)
        with ZipFile(zip_file_path, "w") as zip:
            for file in files:
                zip.write(file, basename(file))

        logger.info(f"Zip file: {zip_name} ... SUCCESS")

        return zip_file_path

    def unzip_files(self, zip_name, destination):
        with ZipFile(zip_name, "r") as zip:
            zip.extractall(destination)
