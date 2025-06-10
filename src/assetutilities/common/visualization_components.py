# Standard library imports
import logging
import copy

# Reader imports
from assetutilities.common.update_deep import update_deep_dictionary
from assetutilities.common.visualization.visualization_polar import VisualizationPolar
from assetutilities.common.visualization.visualization_xy import VisualizationXY

class VisualizationComponents:

    def __init__(self, cfg=None):
        self.cfg = cfg

    def visualization_router(self, cfg):
        logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        # logging.getLogger('matplotlib.font_manager').disabled = True

        logging.info("Starting visualization application ...")

        cfg = self.get_cfg_with_master_data(cfg)

        #TODO Data Transformation
        

        plt_settings = cfg["settings"]
        if "polar" in cfg["settings"]["type"]:
            visualization_polar = VisualizationPolar()
            visualization_polar.polar_plot_set_up_and_save(cfg, plt_settings)
        elif "xy" in cfg["settings"]["type"]:
            visualization_xy = VisualizationXY()
            visualization_xy.xy_plot_set_up_and_save(cfg, plt_settings)
        elif "xy_x_datetime" in cfg["settings"]["type"]:
            visualization_xy = VisualizationXY()
            visualization_xy.xy_plot_set_up_and_save(cfg, plt_settings)

        else:
            raise (Exception("Other plots coding to be completed ... FAIL"))
        
        logging.info("Starting visualization application ...")

    def get_cfg_with_master_data(self, cfg):
        if "master_settings" in cfg:
            master_settings = cfg["master_settings"].copy()
            data_settings = cfg["data"]

            for group_index in range(0, len(data_settings["groups"])):
                group = data_settings["groups"][group_index].copy()
                group = update_deep_dictionary(master_settings["groups"], group)
                data_settings["groups"][group_index] = copy.deepcopy(group)

        return cfg
