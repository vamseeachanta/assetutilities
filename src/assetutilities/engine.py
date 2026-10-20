from __future__ import annotations

# Reader imports
from assetutilities.common.ApplicationManager import ConfigureApplicationInputs
from assetutilities.common.file_management import FileManagement

# Loguru logging shim (issue #28). Drop-in replacement for `logging.info(...)`;
# the run-log file is still configured by ApplicationManager via set_logging.
from assetutilities.common.logging_setup import logger
from assetutilities.common.update_deep import AttributeDict
from assetutilities.common.utilities import save_application_cfg
from assetutilities.common.yml_utilities import (
    WorkingWithYAML,
    resolve_config_placeholders,
)
from assetutilities.engine_registry import registry

library_name = "assetutilities"

app_manager = ConfigureApplicationInputs()
wwyaml = WorkingWithYAML()


def engine(
    inputfile: str | None = None,
    cfg: dict | None = None,
    config_flag: bool = True,
    root_folder: str | None = None,
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

    registry.resolve(basename)

    if embed:
        # ---- EMBEDDABLE RUN PATH (the crux #3282 uses) ----
        # Per-call instance => no module-singleton re-entrancy (does not touch
        # customYaml/CustomInputs). Dispatches the caller cfg directly under the
        # injected root; raises ValueError if cfg/root_folder missing.
        cfg_base = ConfigureApplicationInputs().configure_embed(
            cfg, basename, root_folder, log_to_file=log_to_file
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
        _result_folder_dict, cfg_base = app_manager.configure_result_folder(
            None, cfg_base
        )
    else:
        cfg_base = cfg

    logger.info(f"{basename}, application ... START")

    cfg_base = resolve_config_placeholders(cfg_base)
    cfg_base = registry.dispatch(basename, cfg_base)

    if cfg is None:
        save_application_cfg(cfg_base=cfg_base)

    logger.info(f"{basename}, application ... END")
    cfg_base = app_manager.save_cfg(cfg_base=AttributeDict(cfg_base))
    return cfg_base
