import inspect
import logging
import os
import sys

from loguru import logger


def set_logging(cfg):
    log_level = cfg["default"]["log_level"].upper()
    logNumericLevel = getattr(logging, log_level)

    if not isinstance(logNumericLevel, int):
        raise ValueError("Invalid log level: {}".format(cfg["default"]["log_level"]))

    # Embed/no-file mode: when Analysis.log_to_file is False, log only to stdout
    # and create NO logs/ directory and NO .log file. Default True -> today's
    # forced-file behavior is unchanged (workspace-hub#3297).
    log_to_file = cfg["Analysis"].get("log_to_file", True)

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if log_to_file:
        # Create log directory if not existing (only when writing a file).
        if not os.path.exists(cfg["Analysis"]["log_folder"]):
            os.makedirs(cfg["Analysis"]["log_folder"])

        # Basic configuration for logging
        logfilename = os.path.join(
            cfg["Analysis"]["log_folder"], cfg["Analysis"]["file_name"] + ".log"
        )
        logging.basicConfig(
            # handlers=[InterceptHandler()],
            level=logNumericLevel,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
            filename=logfilename,
            filemode="w",
            force=True,
        )
        loguru_handlers = [
            {
                "sink": sys.stdout,
                "format": "{time} - {name} - {level} - {message}",
                "level": log_level,
            },
            {"sink": logfilename, "serialize": True, "level": log_level},
        ]
    else:
        logging.basicConfig(
            level=logNumericLevel,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
            stream=sys.stdout,
            force=True,
        )
        loguru_handlers = [
            {
                "sink": sys.stdout,
                "format": "{time} - {name} - {level} - {message}",
                "level": log_level,
            },
        ]

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info("Logging started successfully ...")

    config = {
        "handlers": loguru_handlers,
        # "extra": {"user": "someone"},
    }
    logger.configure(**config)
    logger.add(PropagateHandler())

    return cfg


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class PropagateHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)
