# -*- coding: utf-8 -*-
"""
Created on Thu May 17 10:05:12 2018

@author: achantv
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Vamsee Achanta
Date Updated: 2017-11-25
Objective: To set logging level. logLevels can be 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
Outputs: Settings for logging
"""


def set_logging(cfg):
    # Standard library imports
    import logging
    import os
    import sys

    logNumericLevel = getattr(logging, cfg["default"]["log_level"].upper())

    if not isinstance(logNumericLevel, int):
        raise ValueError("Invalid log level: %s" % cfg["default"]["log_level"])

    # Create log directory if not existing
    if not os.path.exists(cfg["Analysis"]["log_folder"]):
        os.makedirs(cfg["Analysis"]["log_folder"])

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Basic configuration for logging
    logfilename = os.path.join(
        cfg["Analysis"]["log_folder"], cfg["Analysis"]["file_name"] + ".log"
    )
    logging.basicConfig(
        level=logNumericLevel,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        filename=logfilename,
        filemode="w",
    )

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info("Logging started successfully ...")

    return cfg