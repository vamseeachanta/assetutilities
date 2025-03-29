# Standard library imports
import datetime
import functools
import logging
import os
import pkgutil
import sys

# Third party imports
import yaml

# Reader imports
from assetutilities.common.data import AttributeDict
from assetutilities.common.data import SaveData
from assetutilities.common.set_logging import set_logging
from assetutilities.common.update_deep import update_deep_dictionary

save_data = SaveData()

def applicationTimer(func):
    # Standard library imports
    import functools

    @functools.wraps(func)
    def wrapper_applicationTimer(*args, **kwargs):
        # Standard library imports
        import time

        start_time = time.perf_counter()

        function_value = func(*args, **kwargs)

        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Finished {func.__name__!r} in {run_time:.2f} secs")

        return function_value

    return wrapper_applicationTimer


def setupApplicationRuns(func):

    @functools.wraps(func)
    def wrapper_applicationRuns(*args, **kwargs):
        # Standard library imports
        import logging

        app_runs = ApplicationRuns(basename=func.__name__)
        logging.info("  ******Set Up Application Runs .... ******")
        cfg = app_runs.configureApplication()
        kwargs["cfg"] = cfg

        # Standard library imports
        import time

        save_results = SaveApplicationResults()

        start_time = time.perf_counter()
        function_value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        if (
            cfg.default.__contains__("data_source")
            and cfg.default["data_source"] == "db"
        ):
            save_results.saveApplicationResultsToDB(
                cfg=kwargs["cfg"], run_time=run_time, run_dict=None
            )

        if (
            cfg.default.__contains__("data_source")
            and cfg.default["data_source"] == "db"
        ):
            run_df = app_runs.getRuns()
            if (run_df is not None) and (len(run_df) > 0):
                for row_index in range(0, len(run_df)):
                    start_time = time.perf_counter()
                    run_dict = run_df.to_dict("records")[row_index]
                    cfg = app_runs.configureApplication(run_dict)
                    kwargs["cfg"] = cfg
                    function_value = func(*args, **kwargs)

                    end_time = time.perf_counter()
                    run_time = end_time - start_time
                    save_results.saveApplicationResultsToDB(
                        cfg=kwargs["cfg"], run_time=run_time, run_dict=run_dict
                    )

        logging.info("  ****** Application Runs .... COMPLETE ******")

        return function_value

    return wrapper_applicationRuns



class ConfigureApplicationInputs:

    def __init__(self):
        pass

    def configure(self, run_dict, library_name, basename, cfg_argv_dict):
        cfg = self.unify_application_and_default_and_custom_yamls(run_dict, library_name, basename, cfg_argv_dict)
        cfg = self.get_application_configuration_parameters(run_dict, basename, cfg)
        cfg = self.configure_overwrite_filenames(cfg)
        cfg = self.convert_cfg_to_attribute_dictionary(cfg)
        cfg = set_logging(cfg)

        logging.debug(cfg)

        return cfg

    def unify_application_and_default_and_custom_yamls(self, run_dict, library_name, basename, cfg_argv_dict):
        application_input_file_path = os.path.join(
            os.getcwd(), "src", library_name, "tests", "test_data", basename + ".yml")
        self.ApplicationInputFile = application_input_file_path
        self.get_custom_file()
        if not os.path.isfile(self.ApplicationInputFile):
            try:
                filename = os.path.join('base_configs', 'modules', basename, basename + '.yml')
                self.ApplicationInputFile = filename
                data = pkgutil.get_data(library_name, self.ApplicationInputFile)
            except Exception:
                raise FileNotFoundError(
                    "Application input file {0} not found".format(
                        self.ApplicationInputFile
                    )
                )
            self.ApplicationInputFile_dict = yaml.safe_load(data)

        # Get updated configuration file for Analysis
        cfg = self.generateYMLInput(run_dict, cfg_argv_dict)

        return cfg

    def get_custom_file(self, run_dict=None):

        try:
            if sys.argv[1] is not None:
                self.customYaml = sys.argv[1]
                print(
                    "Updating default values with contents in file {0}".format(
                        self.customYaml
                    )
                )
        except:
            self.customYaml = None
            print(
                "No update values file is provided. Running program default values "
                "from {0}".format(self.ApplicationInputFile)
            )

        if run_dict is not None:
            self.customYaml = None
            self.CustomInputs = run_dict.get("CustomInputs", None)
        else:
            self.CustomInputs = None

    def generateYMLInput(self, run_dict, cfg_argv_dict):

        if os.path.isfile(self.ApplicationInputFile):
            with open(self.ApplicationInputFile, "r") as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.Loader)
        else:
            cfg = self.ApplicationInputFile_dict

        if self.customYaml is not None:
            try:
                with open(self.customYaml, "r") as ymlfile:
                    cfgCustomValues = yaml.load(ymlfile, Loader=yaml.Loader)
                    default_yaml_file = cfgCustomValues.get("default_yaml", None)

                with open(self.customYaml) as fp:
                    custom_file_data = fp.read()
            except Exception as e:

                print("Update Input file could not be loaded successfully.")
                print("Error is : {}".format(e))
                print("Stopping program")
                sys.exit()
        elif self.CustomInputs is not None:

            custom_file_data = self.CustomInputs.replace("\\'", "'").replace(
                "\\n", "\n"
            )
            default_yaml_file = run_dict["DefaultInputFile"]
        else:
            custom_file_data = ""
            default_yaml_file = None

        if (self.customYaml is not None) or (self.CustomInputs is not None):
            if default_yaml_file is None:
                cfgDefaultAndCustomValues = yaml.load(
                    custom_file_data, Loader=yaml.Loader
                )
            else:
                with open(default_yaml_file) as fp:
                    default_file_data = fp.read()
                custom_and_default_yaml_data = (
                    custom_file_data + "\n" + default_file_data
                )
                cfgDefaultAndCustomValues = yaml.load(
                    custom_and_default_yaml_data, Loader=yaml.Loader
                )

            cfg = update_deep_dictionary(cfg, cfgDefaultAndCustomValues)
            
            cfg = update_deep_dictionary(cfg, cfg_argv_dict)

        return cfg

    def get_application_configuration_parameters(self, run_dict, basename, cfg):

        application_start_time = datetime.datetime.now()

        if self.customYaml is not None:
            custom_file_name = os.path.split(self.customYaml)[1].split(".")[0]
            AnalysisRootFolder = os.path.split(self.customYaml)[0]
            if AnalysisRootFolder == "":
                AnalysisRootFolder = os.getcwd()
        elif self.CustomInputs is not None:
            custom_file_name = run_dict["RunName"]
            AnalysisRootFolder = os.path.join(os.getcwd(), "tests", "cfg", basename)
        else:
            custom_file_name = os.path.split(self.ApplicationInputFile)[1].split(".")[0]
            AnalysisRootFolder = os.getcwd()

        filename_label = cfg.get('meta', {}).get('label', None)
        if filename_label is not None:
            custom_file_name = custom_file_name + "_" + filename_label

        file_name = (
            custom_file_name + "_" + application_start_time.strftime("%Y%m%d_%Hh%Mm")
        )
        file_name_for_overwrite = custom_file_name
        result_folder = os.path.join(AnalysisRootFolder, "results")
        result_data_folder = os.path.join(result_folder, "Data")
        result_plot_folder = os.path.join(result_folder, "Plot")
        result_folder = os.path.join(AnalysisRootFolder, "results")
        log_folder = os.path.join(AnalysisRootFolder, "logs")

        if not os.path.exists(result_folder):
            os.mkdir(result_folder)
        if not os.path.exists(log_folder):
            os.mkdir(log_folder)
        if not os.path.exists(result_data_folder):
            os.mkdir(result_data_folder)
        if not os.path.exists(result_plot_folder):
            os.mkdir(result_plot_folder)

        cfg_array_file_names = None

        application_configuration_parameters = {
            "Analysis": {
                "basename": basename,
                "analysis_root_folder": AnalysisRootFolder,
                "file_name": file_name,
                "file_name_for_overwrite": file_name_for_overwrite,
                "result_folder": result_folder,
                "log_folder": log_folder,
                "start_time": application_start_time,
                "cfg_array_file_names": cfg_array_file_names,
                "DefaultInputFile": cfg.get("default_yaml", None),
                "CustomInputFile": self.customYaml,
            }
        }

        cfg = update_deep_dictionary(cfg, application_configuration_parameters)
        
        return cfg

    def configure_overwrite_filenames(self, cfg):
        if cfg["default"]["config"]["overwrite"]["output"] is True:
            cfg["Analysis"]["file_name"] = cfg["Analysis"][
                "file_name_for_overwrite"
            ]
        try:
            fe_folder = cfg["Analysis"].get("fe_folder", None)
            if fe_folder is None:
                cfg["Analysis"]["fe_folder"] = cfg["Analysis"][
                    "result_folder"
                ]
        except KeyError as e:
            logging.info("No fe_folder key in Analysis section of yml file")
            logging.info("Error is : {}".format(e))

        return cfg

    def convert_cfg_to_attribute_dictionary(self, cfg):
        cfg = AttributeDict(cfg)
        
        return cfg

    def validate_arguments_run_methods(self, inputfile):
        """
        Validate inputs for following run methods:
        - module (i.e. python -m digitalmodel input.yml "{'key':'value'}")
        - from python file (i.e. test_*.py)
        - from function call (i.e. engine(inputfile))
        
        """
        cfg_argv_dict = {}

        if len(sys.argv) > 1 and inputfile is not None:
            raise (
                Exception(
                    "2 Input files provided via arguments & function. Please provide only 1 file ... FAIL"
                )
            )

        if len(sys.argv) > 1:
            try:
                cfg_argv_dict = eval(sys.argv[2])
            except Exception as e:
                print(f"Error: {e}")
                raise("Check dictionary format provided provided in sys.argv[2] ... FAIL")

            if not type(cfg_argv_dict) is dict:
                cfg_argv_dict = {}

            if not os.path.isfile(sys.argv[1]):
                raise (FileNotFoundError(f"Input file {sys.argv[1]} not found ... FAIL"))
            else:
                inputfile = sys.argv[1]

        if len(sys.argv) <= 1:
            if not os.path.isfile(inputfile):
                raise (FileNotFoundError(f"Input file {inputfile} not found ... FAIL"))
            else:
                sys.argv.append(inputfile)
        return inputfile, cfg_argv_dict


    def save_cfg(cfg_base):
        output_dir = cfg_base.Analysis["analysis_root_folder"]

        filename = cfg_base.Analysis["file_name"]
        filename_path = os.path.join(output_dir, "results", filename)

        save_data.saveDataYaml(cfg_base, filename_path, default_flow_style=False)
