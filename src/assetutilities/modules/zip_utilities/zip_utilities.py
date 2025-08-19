import os
from os.path import basename
from zipfile import ZipFile
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import traceback

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
        
        # Check if parallel processing should be used
        use_parallel = len(stem_list) > 1 and cfg.get("parallel_processing", {}).get("enabled", True)
        max_workers = cfg.get("parallel_processing", {}).get("max_workers", "auto")
        
        if max_workers == "auto":
            max_workers = min(cpu_count(), len(stem_list))
        elif isinstance(max_workers, int) and max_workers > 0:
            # Allow configured worker count but cap at reasonable maximum
            max_workers = min(max_workers, len(stem_list))
        else:
            # Fallback to auto-detection for invalid values
            max_workers = min(cpu_count(), len(stem_list))
            logger.warning(f"Invalid max_workers value, auto-detecting: {max_workers}")
        
        if use_parallel:
            logger.info(f"Processing {len(stem_list)} stems in parallel with {max_workers} workers")
            results = self._process_stems_parallel(cfg, stem_list, input_file_directory, input_file_extenstions, max_workers)
        else:
            logger.info(f"Processing {len(stem_list)} stems sequentially")
            results = self._process_stems_sequential(cfg, stem_list, input_file_directory, input_file_extenstions)
        
        # Aggregate results
        cfg[cfg["basename"]] = results

    def _process_stems_parallel(self, cfg, stem_list, input_file_directory, input_file_extenstions, max_workers):
        """Process stems in parallel using ProcessPoolExecutor"""
        results = []
        failed_stems = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all stems for processing
            future_to_stem = {
                executor.submit(
                    self._process_single_stem,
                    cfg,
                    stem,
                    input_file_directory,
                    input_file_extenstions
                ): stem for stem in stem_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_stem):
                stem = future_to_stem[future]
                try:
                    result = future.result()
                    if result.get("error"):
                        failed_stems.append({"stem": stem, "error": result["error"]})
                        logger.error(f"Failed to process stem {stem}: {result['error']}")
                    else:
                        results.append(result)
                        logger.info(f"Successfully processed stem: {stem}")
                except Exception as exc:
                    error_msg = f"Exception during processing: {str(exc)}\n{traceback.format_exc()}"
                    failed_stems.append({"stem": stem, "error": error_msg})
                    logger.error(f"Stem {stem} generated an exception: {exc}")
        
        if failed_stems:
            logger.warning(f"Failed to process {len(failed_stems)} stems out of {len(stem_list)}")
        
        return results

    def _process_stems_sequential(self, cfg, stem_list, input_file_directory, input_file_extenstions):
        """Process stems sequentially (fallback method)"""
        results = []
        
        for stem in stem_list:
            try:
                result = self._process_single_stem(cfg, stem, input_file_directory, input_file_extenstions)
                if result.get("error"):
                    logger.error(f"Failed to process stem {stem}: {result['error']}")
                else:
                    results.append(result)
                    logger.info(f"Successfully processed stem: {stem}")
            except Exception as exc:
                f"Exception during processing: {str(exc)}\n{traceback.format_exc()}"
                logger.error(f"Stem {stem} generated an exception: {exc}")
        
        return results

    @staticmethod
    def _process_single_stem(cfg, stem, input_file_directory, input_file_extenstions):
        """Process a single stem - extracted from original loop logic"""
        try:
            files = []
            for file in os.listdir(input_file_directory):
                for input_file_extension in input_file_extenstions:
                    if file.__contains__(stem) and file.endswith(input_file_extension):
                        file_path = os.path.join(input_file_directory, file)
                        files.append(file_path)

            # Create a ZipUtilities instance for static method context
            zip_util = ZipUtilities()
            zip_file_path = zip_util.zip_files(cfg, files, stem)
            
            return {
                "stem": stem,
                "zip_file_path": zip_file_path,
                "files": files,
                "error": None
            }
        except Exception as exc:
            return {
                "stem": stem,
                "zip_file_path": None,
                "files": [],
                "error": f"Exception: {str(exc)}\n{traceback.format_exc()}"
            }

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
