# Standard library imports
import logging

# Third party imports
import matplotlib.pyplot as plt  # noqa  # noqa
import numpy as np
import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init

# Reader imports
from assetutilities.common.data_management import DataManagement
from assetutilities.common.utilities import is_file_valid_func
from assetutilities.common.visualization.visualization_common import VisualizationCommon

colorama_init()
dm = DataManagement()
visualization_common = VisualizationCommon()


class VisualizationPolar:
    def __init__(self):
        pass

    def polar_plot_set_up_and_save(self, cfg, plt_settings):
        data_df, cfg = self.get_data_df_and_plot_properties(cfg)
        plt_settings["traces"] = int(len(data_df.columns) / 2)
        if cfg["settings"]["plt_engine"] == "plotly":
            plt_properties = self.get_polar_plot_plotly(data_df, plt_settings)
            visualization_common.add_image_to_polar_plot(
                cfg, plt_settings, plt_properties
            )
            self.save_polar_plot_and_close_plotly(plt, cfg)
        elif cfg["settings"]["plt_engine"] == "matplotlib":
            plt_properties = self.get_polar_plot_matplotlib(data_df, plt_settings, cfg)
            visualization_common.add_image_to_polar_plot(
                cfg, plt_settings, plt_properties
            )
            self.save_polar_plot_and_close_matplotlib(plt_properties, cfg)

    def get_data_df_and_plot_properties(self, cfg):
        data_dict, cfg = self.get_polar_mapped_data_dict(cfg)
        data_df = pd.DataFrame.from_dict(data_dict, orient="index").transpose()

        cfg = visualization_common.get_plot_properties_for_df(cfg, data_df)

        return data_df, cfg

    def get_polar_mapped_data_dict(self, cfg):
        if cfg["data"]["type"] == "input":
            data_dict, legend = self.get_polar_mapped_data_dict_from_input(cfg)
            if len(cfg["settings"]["legend"]["label"]) == 0:
                cfg["settings"]["legend"]["label"] = legend

        elif cfg["data"]["type"] == "csv":
            data_dict, cfg = self.get_polar_mapped_data_dict_from_csv(cfg)

        return data_dict, cfg

    def get_polar_mapped_data_dict_from_csv(self, cfg):
        mapped_data_cfg = {}
        theta_data_array = []
        r_data_array = []

        legend_data = []
        for group_cfg in cfg["data"]["groups"]:
            analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
            file_is_valid, valid_file = is_file_valid_func(
                group_cfg["file_name"], analysis_root_folder
            )
            if not file_is_valid:
                logging.error(
                    FileNotFoundError(
                        f"Invalid file name/path: {group_cfg['file_name']}"
                    )
                )
                logging.error(
                    f"Please check the file name/path in the input file: {group_cfg['file_name']}"
                )
                logging.error(
                    f"Program {Fore.RED}continues to run ...{Style.RESET_ALL}"
                )

            else:
                df = pd.read_csv(valid_file)
                df = dm.get_filtered_df(group_cfg, df)
                df = dm.get_transformed_df(group_cfg, df)
                theta_data_dict = df[group_cfg["columns"]["theta"]].to_dict("list")
                r_data_dict = df[group_cfg["columns"]["r"]].to_dict("list")

                theta_legend_array = []
                r_legend_array = []

                for theta_column in group_cfg["columns"]["theta"]:
                    theta_data = theta_data_dict[theta_column]
                    theta_data_array = theta_data_array + [theta_data]

                    if group_cfg["label"] is not None:
                        legend_label = group_cfg["label"] + ", " + theta_column
                    else:
                        legend_label = theta_column
                    theta_legend_array.append(legend_label)

                for r_column in group_cfg["columns"]["r"]:
                    r_data = r_data_dict[r_column]
                    r_data_array = r_data_array + [r_data]

                    if group_cfg["label"] is not None:
                        legend_label = group_cfg["label"] + ", " + r_column
                    else:
                        legend_label = r_column
                    r_legend_array.append(legend_label)

            # Consolidate theta and r data
            if len(group_cfg["columns"]["theta"]) <= len(group_cfg["columns"]["r"]):
                legend_data = legend_data + r_legend_array
            else:
                legend_data = legend_data + theta_legend_array

        if len(cfg["settings"]["legend"]["label"]) == len(legend_data):
            legend_data = cfg["settings"]["legend"]["label"]
            logging.info("Using legend labels from the input file")
        elif len(cfg["settings"]["legend"]["label"]) > 0:
            logging.warning(
                "The number of legend labels is not equal to the number of data columns."
            )
            logging.warning("Ignoring the legend labels in the input file")

        mapped_data_cfg = {
            "data": {"groups": [{"theta": theta_data_array, "r": r_data_array}]}
        }
        cfg["settings"]["legend"]["label"] = legend_data
        data_dict, legend_unused = self.get_polar_mapped_data_dict_from_input(
            mapped_data_cfg
        )

        return data_dict, cfg

    def get_polar_mapped_data_dict_from_input(self, mapped_data_cfg):
        data_dict = {}
        legend = []
        trace_count = 0
        for group_cfg in mapped_data_cfg["data"]["groups"]:
            theta_data = group_cfg["theta"]
            for theta_index in range(0, len(theta_data)):
                new_data = [theta * np.pi / 180 for theta in theta_data[theta_index]]
                theta_data[theta_index] = new_data

            r_data = group_cfg["r"]
            legend_item = group_cfg.get("label", None)
            legend.append(legend_item)

            no_of_trends = max(len(theta_data), len(r_data))

            if len(theta_data) < len(r_data):
                theta_data = [theta_data[0]] * len(r_data)
            if len(theta_data) > len(r_data):
                r_data = [r_data[0]] * len(theta_data)

            for i in range(0, no_of_trends):
                data_dict.update({"theta_" + str(i + trace_count): theta_data[i]})
                data_dict.update({"r_" + str(i + trace_count): r_data[i]})
            trace_count += no_of_trends

        return data_dict, legend

    def get_axis_for_polar(self, rect):
        rect_polar = rect.copy()
        rect_polar[0] = rect[0] * np.pi / 180
        rect_polar[1] = rect[1] * np.pi / 180

        return rect_polar

    def get_polar_plot_plotly(self, df, plt_settings):
        if "plt_kind" in plt_settings and plt_settings["plt_kind"] == "polar":
            # Radial line

            plt.polar(df["x"], df["y"], label=plt_settings["label"])
        elif plt_settings["plt_kind"] == "polar_scatter":
            # Radial scatter
            # Third party imports
            import plotly.express as px

            plt = px.scatter_polar(df, r=df["r_0"], theta=df["theta_0"])

        plt_properties = {"plt": plt, "fig": None}

        return plt_properties

    def get_polar_plot_matplotlib(self, df, plt_settings, cfg):
        # Third party imports
        import matplotlib.pyplot as plt  # noqa

        if (
            "plt_properties" in plt_settings
            and plt_settings["plt_properties"]["plt"] is not None
        ):
            plt = plt_settings["plt_properties"]["plt"]

        # Add axis for plot

        alpha = plt_settings.get("alpha", 1)
        facecolor = plt_settings.get("facecolor", None)
        if ("add_axes" not in plt_settings) or (not plt_settings["add_axes"]):
            fig, ax = plt.subplots(
                subplot_kw={"projection": "polar"}, facecolor=facecolor, alpha=alpha[0]
            )

        else:
            fig = plt_settings["plt_properties"]["fig"]
            rect = plt_settings["rect"]
            ax = fig.add_axes(rect, polar=True, facecolor=facecolor, alpha=alpha[0])

            axis = plt_settings["axis"]
            if axis != "off":
                axis = self.get_axis_for_polar(axis)
            plt.axis(axis)

        # Add trace or plot style
        for index in range(0, plt_settings["traces"]):
            label = None
            if "legend" in plt_settings:
                label = plt_settings["legend"]["label"][index]

            if plt_settings["type"] == "polar":
                ax.plot(
                    df["theta_" + str(index)],
                    df["r_" + str(index)],
                    label=label,
                    color=plt_settings["color"][index],
                    linestyle=plt_settings["linestyle"][index],
                    alpha=plt_settings["alpha"][index],
                )
            elif plt_settings["type"] == "polar_scatter":
                ax.scatter(
                    df["theta_" + str(index)],
                    df["r_" + str(index)],
                    label=label,
                    color=plt_settings["color"][index],
                    linestyle=plt_settings["linestyle"][index],
                    alpha=plt_settings["alpha"][index],
                )

        legend_flag = True
        if "legend" in plt_settings:
            legend_flag = plt_settings["legend"].get("flag", True)
        if legend_flag:
            ax.legend(loc="best")
            prop = None
            if "legend" in plt_settings and "prop" in plt_settings["legend"]:
                prop = plt_settings["legend"].get("prop", None)
            if prop is not None:
                plt.legend(prop=prop)

        plt = visualization_common.get_plt_with_arrows(plt, plt_settings)

        set_rmax = plt_settings.get("set_rmax", None)
        if set_rmax is not None:
            ax.set_rmax(set_rmax)

        set_rticks = plt_settings.get("set_rticks", None)
        if set_rticks is not None:
            ax.set_rticks(set_rticks)

        set_rlabel_position = plt_settings.get("set_rlabel_position", None)
        if set_rlabel_position is not None:
            ax.set_rlabel_position(set_rlabel_position)

        set_theta_zero_location = plt_settings.get("set_theta_zero_location", None)
        if set_theta_zero_location is not None:
            ax.set_theta_zero_location(set_theta_zero_location)

        set_thetagrids = plt_settings.get("set_thetagrids", None)
        if set_thetagrids is not None:
            ax.set_thetagrids(set_thetagrids)

        set_theta_zero_location = plt_settings.get("set_theta_zero_location", None)
        if set_theta_zero_location is not None:
            ax.set_theta_zero_location(set_theta_zero_location)

        set_theta_direction = plt_settings.get("set_theta_direction", None)
        if set_theta_direction is not None:
            ax.set_theta_direction(set_theta_direction)

        set_thetamin = plt_settings.get("set_thetamin", None)
        if set_thetamin is not None:
            ax.set_thetamin(set_thetamin)

        set_thetamax = plt_settings.get("set_thetamax", None)
        if set_thetamax is not None:
            ax.set_thetamax(set_thetamax)

        grid = plt_settings.get("grid", True)
        ax.grid(grid)

        title = plt_settings.get("title", None)
        if title is not None:
            ax.set_title(plt_settings["title"], va="bottom")

        plt_properties = {"plt": plt, "fig": fig}
        if "add_axes" in cfg and len(cfg.add_axes) > 0:
            visualization_common.add_axes_to_plt(plt_properties, cfg)

        plt_properties = {"plt": plt, "fig": fig, "ax": ax}

        return plt_properties

    def save_polar_plot_and_close_plotly(self, plt, cfg):
        plot_name_paths = self.get_plot_name_path(cfg)
        for file_name in plot_name_paths:
            # plt.write_image(file_name)
            plt.write_html(file_name)

            plt.savefig(file_name, dpi=100)

        plt.close()

    def save_polar_plot_and_close_matplotlib(self, plt_properties, cfg):
        plot_name_paths = visualization_common.get_plot_name_path(cfg)

        plt = plt_properties["plt"]
        for file_name in plot_name_paths:
            plt.savefig(file_name, dpi=800)

        plt.close()
