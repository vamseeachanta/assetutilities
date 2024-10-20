# Standard library imports
import logging
import math

# Third party imports
import matplotlib.pyplot as plt  # noqa
import pandas as pd  # noqa

# Reader imports
from assetutilities.common.data_management import DataManagement
from assetutilities.common.utilities import is_file_valid_func
from assetutilities.common.visualization.visualization_common import VisualizationCommon

dm = DataManagement()
visualization_common = VisualizationCommon()


class VisualizationXY:

    def __init__(self):
        pass

    def xy_plot_set_up_and_save(self, cfg, plt_settings):
        data_df, cfg = self.get_data_df_and_plot_properties(cfg)
        # if cfg['settings']['plt_engine'] == 'plotly':
        #     plt = self.get_xy_plot_plotly(data_df, plt_settings)
        #     self.save_xy_plot_and_close_plotly(plt, cfg)
        if cfg["settings"]["plt_engine"] == "matplotlib":
            plt_properties = self.get_xy_plot_matplotlib(data_df, plt_settings, cfg)
            self.save_xy_plot_and_close_matplotlib(plt_properties, cfg)
        else:
            raise ValueError("Invalid plt_engine")

    def get_data_df_and_plot_properties(self, cfg):
        if cfg["data"]["type"] == "input":
            data_dict = self.get_xy_mapped_data_dict_from_input(cfg)
            data_df = pd.DataFrame.from_dict(data_dict, orient="index").transpose()
        elif cfg["data"]["type"] == "csv":
            data_dict, cfg = self.get_xy_mapped_data_dict_from_csv(cfg)
            data_df = pd.DataFrame.from_dict(data_dict, orient="index").transpose()

        cfg = visualization_common.get_plot_properties_for_df(cfg, data_df)

        return data_df, cfg

    def get_xy_mapped_data_dict_from_input(self, mapped_data_cfg):
        data_dict = {}

        for group_cfg in mapped_data_cfg["data"]['groups']:
            x_data = group_cfg["x"]
            y_data = group_cfg["y"]

            no_of_trends = max(len(x_data), len(y_data))

            if len(x_data) < len(y_data):
                x_data = [x_data[0]] * len(y_data)
            if len(x_data) > len(y_data):
                y_data = [y_data[0]] * len(x_data)

            for i in range(0, no_of_trends):
                data_dict.update({"x_" + str(i): x_data[i]})
                data_dict.update({"y_" + str(i): y_data[i]})

        return data_dict

    def get_xy_mapped_data_dict_from_csv(self, cfg):
        mapped_data_cfg = {}
        x_data_array = []
        y_data_array = []

        legend_data = []
        for group_cfg in cfg["data"]["groups"]:
            analysis_root_folder = cfg["Analysis"]["analysis_root_folder"]
            file_is_valid, valid_file = is_file_valid_func(
                group_cfg["file_name"], analysis_root_folder
            )
            if not file_is_valid:
                raise ValueError(f'Invalid file name/path: {group_cfg["file_name"]}')

            df = pd.read_csv(valid_file)
            df = dm.get_filtered_df(group_cfg, df)
            df = dm.get_transformed_df(group_cfg, df)
            x_data_dict = df[group_cfg["columns"]["x"]].to_dict("list")
            y_data_dict = df[group_cfg["columns"]["y"]].to_dict("list")

            x_legend_array = []
            y_legend_array = []

            for x_column in group_cfg["columns"]["x"]:
                x_data = x_data_dict[x_column]
                x_data_array = x_data_array + [x_data]

                legend_label = group_cfg["label"] + ", " + x_column
                x_legend_array.append(legend_label)

            for y_column in group_cfg["columns"]["y"]:
                y_data = y_data_dict[y_column]
                y_data_array = y_data_array + [y_data]

                legend_label = group_cfg["label"] + ", " + y_column
                y_legend_array.append(legend_label)

            # Consolidate x and y data
            if len(group_cfg["columns"]["x"]) <= len(group_cfg["columns"]["y"]):
                legend_data = legend_data + y_legend_array
            else:
                legend_data = legend_data + x_legend_array

        if len(cfg["settings"]["legend"]["label"]) == len(legend_data):
            legend_data = cfg["settings"]["legend"]["label"]
            logging.info("Using legend labels from the input file")
        elif len(cfg["settings"]["legend"]["label"]) > 0:
            logging.warning(
                "The number of legend labels is not equal to the number of data columns."
            )
            logging.warning("Ignoring the legend labels in the input file")

        mapped_data_cfg = {"data": {"groups": [{"x": x_data_array, "y": y_data_array}]}}
        cfg["settings"]["legend"]["label"] = legend_data
        data_dict = self.get_xy_mapped_data_dict_from_input(mapped_data_cfg)

        return data_dict, cfg

    def get_xy_plot_matplotlib(self, df, plt_settings, cfg):
        # Third party imports
        import matplotlib.pyplot as plt  # noqa

        if (
            "plt_properties" in plt_settings
            and plt_settings["plt_properties"]["plt"] is not None
        ):
            plt = plt_settings["plt_properties"]["plt"]

        fig, ax = plt.subplots()

        # Add trace or plot style
        plt_settings["traces"] = int(len(df.columns) / 2)

        color_list = cfg["settings"]["color"]
        linestyle_list = cfg["settings"]["linestyle"]
        if len(linestyle_list) < plt_settings["traces"]:
            linestyle_list = linestyle_list * math.ceil(plt_settings["traces"]/len(linestyle_list))
        alpha_list = cfg["settings"]["alpha"]
        markerprops_list = cfg["settings"]["markerprops"]
        if len(markerprops_list) < plt_settings["traces"]:
            markerprops_list = markerprops_list * math.ceil(plt_settings["traces"]/len(markerprops_list))

        plot_mode = cfg["settings"].get("mode", ["line"])

        for index in range(0, plt_settings["traces"]):
            
            linestyle = linestyle_list[index]
            marker_style = dict(
                color=color_list[index],
                linestyle=linestyle_list[index],
                marker=markerprops_list[index]["marker"],
                markersize=markerprops_list[index]["markersize"],
                markerfacecoloralt=None,
                fillstyle="none",
            )

            if "line" in plot_mode and "scatter" in plot_mode:
                ax.plot(
                    df["x_" + str(index)],
                    df["y_" + str(index)],
                    label=plt_settings["legend"]["label"][index],
                    alpha=alpha_list[index],
                    **marker_style,
                )
            elif "line" in plot_mode:
                ax.plot(
                    df["x_" + str(index)],
                    df["y_" + str(index)],
                    label=plt_settings["legend"]["label"][index],
                    color=color_list[index],
                    linestyle=linestyle_list[index],
                    alpha=alpha_list[index],
                )

            elif "scatter" in plot_mode:
                ax.scatter(
                    df["x_" + str(index)],
                    df["y_" + str(index)],
                    label=plt_settings["legend"]["label"][index],
                    color=color_list[index],
                    edgecolors=color_list[index],
                    facecolors="none",
                    marker=markerprops_list[index]["marker"],
                    s=markerprops_list[index]["markersize"],
                    alpha=alpha_list[index],
                )

        grid = plt_settings.get("grid", True)
        ax.grid(grid)

        title = plt_settings.get("title", None)
        if title is not None:
            ax.set_title(title, va="bottom")
        suptitle = plt_settings.get("suptitle", None)
        if suptitle is not None:
            fig.suptitle(suptitle)

        legend_settings = plt_settings.get("legend", None)
        legend_flag = legend_settings.get("flag", True)
        if legend_flag:
            loc = plt_settings["legend"].get("loc", "best")
            ax.legend(loc=loc)
            prop = plt_settings["legend"].get("prop", None)
            if prop is not None:
                framealpha = plt_settings["legend"].get("framealpha", 0.5)
                plt.legend(prop=prop, framealpha=framealpha)

        plt_properties = {"plt": plt, "fig": fig}
        if "add_axes" in cfg and len(cfg.add_axes) > 0:
            self.add_axes_to_plt(plt_properties, cfg)

        ax.set(
            xlabel=plt_settings.get("xlabel", None),
            ylabel=plt_settings.get("ylabel", None),
        )
        ax.label_outer()

        plt = visualization_common.add_x_y_lim_formats(cfg, plt)
        
        plt_properties = {"plt": plt, "fig": fig}
        return plt_properties

    def save_xy_plot_and_close_matplotlib(self, plt_properties, cfg):
        plot_name_paths = visualization_common.get_plot_name_path(cfg)
        plt = plt_properties["plt"]
        for file_name in plot_name_paths:
            plt.savefig(file_name, dpi=800)

    def resolve_legends(self):
        # TODO Resolve legends in a comprehensive manner
        # Get legend data
        if "legend" in mapped_data_cfg["data"]:
            legend_data = mapped_data_cfg["data"]["legend"]
        elif "legend_data" in mapped_data_cfg:
            legend_data = mapped_data_cfg["legend_data"]
        else:
            legend_data = []

        no_of_trends = max(len(x_data), len(y_data))

        if not len(legend_data) == no_of_trends:
            legend_data = ["legend_" + str(i) for i in range(0, no_of_trends)]

