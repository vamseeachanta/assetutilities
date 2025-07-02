# Standard library imports
import logging

# Reader imports
from assetutilities.common.ApplicationManager import ConfigureApplicationInputs
from assetutilities.common.download_data.dwnld_from_zipurl import DownloadDataFromURL
from assetutilities.common.file_edit import FileEdit
from assetutilities.common.file_management import FileManagement
from assetutilities.common.text_analytics import TextAnalytics
from assetutilities.common.update_deep import AttributeDict
from assetutilities.common.utilities import save_application_cfg
from assetutilities.common.visualization_components import VisualizationComponents
from assetutilities.common.webscraping.web_scraping import WebScraping
from assetutilities.common.yml_utilities import WorkingWithYAML
from assetutilities.modules.data_exploration.data_exploration import DataExploration
from assetutilities.modules.zip_utilities.zip_utilities import ZipUtilities
from assetutilities.modules.csv_utilities.csv_utilities_router import CSVUtilitiesRouter

library_name = "assetutilities"

app_manager = ConfigureApplicationInputs()
de = DataExploration()
fm = FileManagement()
wwyaml = WorkingWithYAML()


def engine(inputfile: str = None, cfg: dict = None, config_flag: bool = True) -> dict:

    cfg_argv_dict = {}
    if cfg is None:
        inputfile, cfg_argv_dict = app_manager.validate_arguments_run_methods(inputfile)
        cfg = wwyaml.ymlInput(inputfile, updateYml=None)
        cfg = AttributeDict(cfg)
        if cfg is None:
            raise ValueError("cfg is None")

    if 'basename' in cfg:
        basename = cfg["basename"]
    elif 'meta' in cfg:
        basename = cfg["meta"]["basename"]
    else:
        raise ValueError("basename not found in cfg")

    if config_flag:
        fm = FileManagement()
        cfg_base = app_manager.configure(cfg, library_name, basename, cfg_argv_dict)
        cfg_base = fm.router(cfg_base)
        result_folder_dict, cfg_base = app_manager.configure_result_folder(None, cfg_base)
    else:
        cfg_base = cfg

    logging.info(f"{basename}, application ... START")

    if basename in ["excel_utilities"]:
        # Reader imports
        from assetutilities.modules.excel_utilities.excel_utilities import ExcelUtilities
        eu = ExcelUtilities()
        cfg_base = eu.excel_utility_router(cfg_base)
    elif basename in ["visualization"]:
        viz_comp = VisualizationComponents()
        viz_comp.visualization_router(cfg_base)
    elif basename in ["file_management"]:
        fm.router(cfg_base)
    elif basename in ["file_edit"]:
        fe = FileEdit()
        fe.router(cfg_base)
    elif basename in ["gitpython"]:
        # Reader imports
        from assetutilities.tools.git.git_python_utilities import GitPythonUtilities
        gpu = GitPythonUtilities()
        gpu.router(cfg_base)
    elif basename in ["text_analytics"]:
        ta = TextAnalytics()
        ta.router(cfg_base)
    elif basename in ["word_utilities"]:
        # Reader imports
        from assetutilities.common.word_utilities import WordUtilities

        wu = WordUtilities()
        wu.router(cfg_base)
    elif basename == "data_exploration":
        cfg_base = de.router(cfg_base)

    elif basename == "web_scraping":
        ws = WebScraping()
        cfg_base = ws.router(cfg_base)

    elif basename == "download_data":
        ddfu = DownloadDataFromURL()
        cfg_base = ddfu.router(cfg_base)

    elif basename == "yaml_utilities" or basename == "yml_utilities":
        cfg_base = wwyaml.router(cfg_base)

    elif basename == "reportgen":
        from assetutilities.common.reportgen import reportgen
        # init and run reportgen using config
        reportgen.run(cfg_base)
    elif basename == "zip_utilities":
        zu = ZipUtilities()
        cfg_base = zu.router(cfg_base)
    
    elif basename == "csv_utilities":
        csv_utilities_router = CSVUtilitiesRouter()
        cfg_base = csv_utilities_router.router(cfg_base)

    else:
        raise (Exception(f"Analysis for basename: {basename} not found. ... FAIL"))

    if cfg is None:
        save_application_cfg(cfg_base=cfg_base)

    logging.info(f"{basename}, application ... END")
    cfg_base = app_manager.save_cfg(cfg_base=cfg_base)
    return cfg_base
