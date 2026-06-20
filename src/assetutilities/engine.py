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
from assetutilities.modules.csv_utilities.csv_utilities_router import CSVUtilitiesRouter
from assetutilities.modules.data_exploration.data_exploration import DataExploration
from assetutilities.modules.zip_utilities.zip_utilities import ZipUtilities

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

    if "basename" in cfg:
        basename = cfg["basename"]
    elif "meta" in cfg:
        basename = cfg["meta"]["basename"]
    else:
        raise ValueError("basename not found in cfg")

    if config_flag:
        fm = FileManagement()
        cfg_base = app_manager.configure(cfg, library_name, basename, cfg_argv_dict, inputfile)
        cfg_base = fm.router(cfg_base)
        result_folder_dict, cfg_base = app_manager.configure_result_folder(
            None, cfg_base
        )
    else:
        cfg_base = cfg

    logging.info(f"{basename}, application ... START")

    if basename in ["excel_utilities"]:
        # Reader imports
        from assetutilities.modules.excel_utilities.excel_utilities import (
            ExcelUtilities,
        )

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
        # NOTE: this handler points at a module that does not exist in this
        # package (`assetutilities.tools.git.git_python_utilities`), so it
        # previously raised an opaque ModuleNotFoundError on dispatch. There is
        # no GitPythonUtilities implementation to wire up, so fail loudly with
        # actionable guidance instead of mis-routing. See issue #91.
        raise NotImplementedError(
            "basename 'gitpython' is a stub: no handler is implemented "
            "(expected 'assetutilities.tools.git.git_python_utilities."
            "GitPythonUtilities', which does not exist). Implement that module "
            "and re-wire this branch before using the 'gitpython' workflow."
        )
    elif basename in ["read_pdf"]:
        # Reader imports (lazy: pulls optional PDF deps such as tabula/PyPDF2)
        from assetutilities.modules.pdf_utilities.read_pdf import ReadPDF

        read_pdf = ReadPDF()
        cfg_base["result"] = read_pdf.read_pdf(cfg_base)
    elif basename in ["edit_pdf"]:
        # Reader imports (lazy: pulls optional PDF dep PyPDF2)
        from assetutilities.modules.pdf_utilities.edit_pdf import EditPDF

        edit_pdf = EditPDF()
        edit_pdf.edit_pdf(cfg_base)
    elif basename in ["text_analytics"]:
        # The TextAnalytics.router/get_subset_files methods are no-op stubs
        # (`pass`), so dispatching here silently produced no output. Fail loudly
        # until a real implementation is wired up. See issue #91.
        raise NotImplementedError(
            "basename 'text_analytics' is a stub: "
            "TextAnalytics.get_subset_files is a no-op and produces no output. "
            "Implement assetutilities.common.text_analytics.TextAnalytics "
            "before using the 'text_analytics' workflow."
        )
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
        # CSVUtilitiesRouter.router is a no-op stub (the only branch is `pass`);
        # the real CSVUtilities helper reads a zip file-object, not a path, and
        # produces no standalone output. Fail loudly rather than silently
        # returning an unchanged cfg. See issue #91.
        raise NotImplementedError(
            "basename 'csv_utilities' is a stub: CSVUtilitiesRouter.router is a "
            "no-op and produces no output (the underlying CSVUtilities is an "
            "internal helper for zip_utilities that reads a zip file-object, "
            "not a standalone path). Implement a real router before using the "
            "'csv_utilities' workflow."
        )

    else:
        raise (Exception(f"Analysis for basename: {basename} not found. ... FAIL"))

    if cfg is None:
        save_application_cfg(cfg_base=cfg_base)

    logging.info(f"{basename}, application ... END")
    cfg_base = app_manager.save_cfg(cfg_base=cfg_base)
    return cfg_base
