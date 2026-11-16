# Reader imports
from assetutilities.common.ApplicationManager import ConfigureApplicationInputs

# Loguru logging shim (issue #28). Drop-in replacement for `logging.info(...)`;
# the run-log file is still configured by ApplicationManager via set_logging.
from assetutilities.common.logging_setup import logger
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


def engine(
    inputfile: str = None,
    cfg: dict = None,
    config_flag: bool = True,
    root_folder: str = None,
    log_to_file: bool = True,
    embed: bool = False,
) -> dict:
    """Run an assetutilities workflow.

    Additive params (workspace-hub#3297); defaults are byte-identical to today's
    behavior:

    - ``root_folder`` (default None): on the file/default path, explicitly
      override the resolved ``analysis_root_folder`` so all outputs land under
      this dir. None => today's os.getcwd()/input-file-dir resolution.
    - ``log_to_file`` (default True): consumed only by the ``embed`` path; the
      file/default path keeps its forced-file logging regardless.
    - ``embed`` (default False): when True, dispatch the caller's in-memory
      ``cfg`` directly under ``root_folder`` (re-entrant, sandboxed, no-file
      logging) -- the embeddable run path #3282 consumes.
    """
    cfg_argv_dict = {}
    loaded_from_file = cfg is None
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

    if embed:
        # ---- EMBEDDABLE RUN PATH (the crux #3282 uses) ----
        # Per-call instance => no module-singleton re-entrancy (does not touch
        # customYaml/CustomInputs). Dispatches the caller cfg directly under the
        # injected root; raises ValueError if cfg/root_folder missing.
        cfg_base = ConfigureApplicationInputs().configure_embed(
            cfg,
            basename,
            root_folder,
            log_to_file=log_to_file,
            placeholders_resolved=loaded_from_file,
        )
        fm = FileManagement()
        cfg_base = fm.router(cfg_base)
    elif config_flag:
        fm = FileManagement()
        cfg_base = app_manager.configure(
            cfg,
            library_name,
            basename,
            cfg_argv_dict,
            inputfile,
            root_folder=root_folder,
        )
        cfg_base = fm.router(cfg_base)
        result_folder_dict, cfg_base = app_manager.configure_result_folder(
            None, cfg_base
        )
    else:
        cfg_base = cfg

    logger.info(f"{basename}, application ... START")

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
        from assetutilities.modules.git_utilities.git_utilities import GitUtilities

        cfg_base = GitUtilities().router(cfg_base)
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
        cfg_base = TextAnalytics().router(cfg_base)
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
        cfg_base = CSVUtilitiesRouter().router(cfg_base)

    else:
        raise (Exception(f"Analysis for basename: {basename} not found. ... FAIL"))

    if cfg is None:
        save_application_cfg(cfg_base=cfg_base)

    logger.info(f"{basename}, application ... END")
    cfg_base = app_manager.save_cfg(cfg_base=cfg_base)
    return cfg_base
