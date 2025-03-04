# Standard library imports
import logging
from loguru import logger
import os
import sys

# Reader imports
from assetutilities.common.ApplicationManager import ConfigureApplicationInputs
from assetutilities.common.data import SaveData
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

library_name = "assetutilities"

de = DataExploration()
fm = FileManagement()
save_data = SaveData()
wwyaml = WorkingWithYAML()


def engine(inputfile: str = None, cfg: dict = None, config_flag: bool = True) -> dict:
    if cfg is None:
        inputfile = validate_arguments_run_methods(inputfile)
        cfg = wwyaml.ymlInput(inputfile, updateYml=None)
        cfg = AttributeDict(cfg)
        if cfg is None:
            raise ValueError("cfg is None")

    basename = cfg["basename"]
    application_manager = ConfigureApplicationInputs(basename)
    application_manager.configure(cfg, library_name)

    if config_flag:
        fm = FileManagement()
        cfg_base = application_manager.cfg
        cfg_base = fm.router(cfg_base)
    else:
        cfg_base = cfg

    logger.info(f"{basename}, application ... START")

    if basename in ["excel_utilities"]:
        # Reader imports
        from assetutilities.common.excel_utilities import ExcelUtilities
        eu = ExcelUtilities()
        cfg_base = eu.excel_utility_router(cfg_base)
    elif basename in ["visualization"]:
        viz_comp = VisualizationComponents()
        viz_comp.visualization_router(cfg_base)
    # elif basename in ["read_pdf"]:
    #     read_pdf = ReadPDF()
    #     read_pdf.read_pdf(cfg_base)
    elif basename in ["file_management"]:
        fm = FileManagement()
        fm.router(cfg_base)
    elif basename in ["file_edit"]:
        fe = FileEdit()
        fe.router(cfg_base)
    # elif basename in ["edit_pdf"]:
    #     edit_pdf = EditPDF()
    #     edit_pdf.edit_pdf(cfg_base)
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
    elif cfg["basename"] == "data_exploration":
        cfg_base = de.router(cfg_base)

    elif cfg["basename"] == "web_scraping":
        ws = WebScraping()
        cfg_base = ws.router(cfg_base)

    elif cfg["basename"] == "download_data":
        ddfu = DownloadDataFromURL()
        cfg_base = ddfu.router(cfg_base)

    elif cfg["basename"] == "yaml_utlities" or cfg["basename"] == "yml_utilities":
        cfg_base = wwyaml.router(cfg_base)

    elif cfg["basename"] == "reportgen":
        from assetutilities.common.reportgen import reportgen
        # init and run reportgen using config
        reportgen.run(cfg_base)
    elif cfg["basename"] == "zip_utilities":
        zu = ZipUtilities()
        cfg_base = zu.router(cfg_base)

    else:
        raise (Exception(f"Analysis for basename: {basename} not found. ... FAIL"))

    if cfg is None:
        save_application_cfg(cfg_base=cfg_base)

    logger.info(f"{basename}, application ... END")
    save_cfg(cfg_base=cfg_base)

    return cfg_base


def validate_arguments_run_methods(inputfile):
    """
    Validate inputs for following run methods:
    - module (i.e. python -m digitalmodel input.yml)
    - from python file (i.e. )
    """

    if len(sys.argv) > 1 and inputfile is not None:
        raise (
            Exception(
                "2 Input files provided via arguments & function. Please provide only 1 file ... FAIL"
            )
        )

    if len(sys.argv) > 1:
        if not os.path.isfile(sys.argv[1]):
            raise (FileNotFoundError(f"Input file {sys.argv[1]} not found ... FAIL"))
        else:
            inputfile = sys.argv[1]

    if len(sys.argv) <= 1:
        if not os.path.isfile(inputfile):
            raise (FileNotFoundError(f"Input file {inputfile} not found ... FAIL"))
        else:
            sys.argv.append(inputfile)
    return inputfile


def save_cfg(cfg_base):
    output_dir = cfg_base.Analysis["analysis_root_folder"]

    filename = cfg_base.Analysis["file_name"]
    filename_path = os.path.join(output_dir, "results", filename)

    save_data.saveDataYaml(cfg_base, filename_path, default_flow_style=False)
