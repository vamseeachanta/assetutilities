# Standard library imports
import os

# Third party imports
import matplotlib.pyplot as plt  # noqa
import numpy as np
import pandas as pd  # noqa
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image


class VisualizationCommon:

    def __init__(self):
        pass

    def add_legend(self, plt, plt_settings):
        if plt_settings.__contains__("legend") and plt_settings["legend"]:
            if plt_settings.__contains__("legend_location"):
                legend_location = plt_settings["legend_location"]
            else:
                legend_location = None

            if legend_location == "lower center":
                plt.legend(loc="best", fontsize=8)
            elif (legend_location is None) or (legend_location == "best"):
                plt.legend(loc="best", fontsize=8)

        return plt

    def future_functions(self):
        # TODO
        self.add_title_and_axis_labels()
        self.add_legend()
        self.add_x_y_lim_formats()
        self.add_reference_lines_and_spans()
        self.add_markers
        self.save_and_close()

    def add_x_y_scale_formats(self):
        if self.plt_settings.__contains__("yscale"):
            if self.plt_settings["yscale"]["log"]:
                self.plt.yscale("log")
        if self.plt_settings.__contains__("xscale"):
            if self.plt_settings["xscale"]["log"]:
                self.plt.xscale("log")

    def add_x_y_lim_formats(self, cfg, plt):
        if cfg.settings.__contains__("ylim"):
            ylim = cfg.settings.get("ylim", None)
            if ylim is not None:
                if plt.__name__ == 'matplotlib.pyplot':
                    plt.ylim(ylim)
                else:
                    plt.set_ylim(ylim)
        if cfg.settings.__contains__("xlim"):
            xlim = cfg.settings.get("xlim", None)
            if xlim is not None:
                if plt.__name__ == 'matplotlib.pyplot':
                    plt.xlim(xlim)
                else:
                    plt.set_xlim(xlim)

        return plt

    def add_axes_to_plt(self, plt_properties, cfg):
        for axes_idx in range(0, len(cfg.add_axes)):
            cfg_plt = cfg.add_axes[axes_idx]
            plt_settings = cfg_plt["settings"]
            plt_settings.update({"add_axes": True})
            plt_settings.update({"plt_properties": plt_properties})

            # data_df = self.get_polar_data(cfg_plt)
            # plt_settings["traces"] = int(len(data_df.columns) / 2)

            # plt = self.get_polar_plot_matplotlib(data_df, plt_settings, cfg_plt)

    def get_plt_with_arrows(self, plt, plt_settings):

        # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.arrow.html
        # Add arrows with direct data
        # Try inset_axes: https://matplotlib.org/2.0.2/examples/pylab_examples/axes_demo.html
        if "arrows" not in plt_settings:
            return plt

        arrows = plt_settings["arrows"]
        for arrow in arrows:
            # arr1 = plt.arrow(3, 0, 5, 45, color='blue')
            # # arrow at 45 degree
            theta = arrow["theta"]
            r = arrow["r"]
            color = arrow["color"]

            arr = plt.arrow(
                theta[0] / 180.0 * np.pi,
                r[0],
                theta[1] / 180.0 * np.pi,
                r[1] - r[0],
                alpha=0.75,
                width=0.015,
                color=color,
                lw=2,
                zorder=5,
            )

        return plt

    def get_plot_name_path(self, cfg):
        file_name = cfg["settings"]["file_name"]
        if file_name is None:
            file_name = cfg["Analysis"]["file_name"]
        extensions = cfg["settings"]["plt_save_extensions"]
        plot_folder = os.path.join(cfg["Analysis"]["result_folder"], "Plot")

        plot_name_paths = [
            os.path.join(plot_folder, file_name + extension) for extension in extensions
        ]

        return plot_name_paths

    def add_annotations(self):
        """
        https://matplotlib.org/stable/gallery/text_labels_and_annotations/annotation_demo.html
        #TODO abstract annotation and move to another function.
        or use graphics?
        """
        ax.annotate(
            "a polar annotation",
            xy=(30, 5),  # theta, radius
            xytext=(0.05, 0.05),  # fraction, fraction
            textcoords="figure fraction",
            arrowprops=dict(facecolor="black", shrink=0.05),
            horizontalalignment="left",
            verticalalignment="bottom",
        )

    def get_colors(self, set="single", n=15):
        """
        https://help.tableau.com/current/pro/desktop/en-us/formatting_create_custom_colors.htm
        """
        # Third party imports
        from webcolors import rgb_to_hex

        if set == "single":
            if n <= 10:
                colors = [
                    "#17becf",
                    "#bcbd22",
                    "#7f7f7f",
                    "#e377c2",
                    "#8c564b",
                    "#9467bd",
                    "#d62728",
                    "#2ca02c",
                    "#ff7f0e",
                    "#1f77b4",
                ]
            else:
                colors = [
                    (31, 119, 180),
                    (174, 199, 232),
                    (255, 127, 14),
                    (255, 187, 120),
                    (44, 160, 44),
                    (152, 223, 138),
                    (214, 39, 40),
                    (255, 152, 150),
                    (148, 103, 189),
                    (197, 176, 213),
                    (140, 86, 75),
                    (196, 156, 148),
                    (227, 119, 194),
                    (247, 182, 210),
                    (127, 127, 127),
                    (199, 199, 199),
                    (188, 189, 34),
                    (219, 219, 141),
                    (23, 190, 207),
                    (158, 218, 229),
                ]
                colors = [rgb_to_hex(color) for color in colors]
            colors = colors[0:n]
        elif set == "multi":
            if n <= 8:
                color_1 = ["#0F6BE9", "#043F8F", "#001E45"]
                color_2 = ["#D1350A", "#B23000", "#2F1202"]
                color_3 = ["#A06900", "#5D4101", "#2C1B07"]
                color_4 = ["#05B25D", "#044B32", "#012B1"]
                color_5 = ["#A37BFA", "#492D99", "#019OA52"]
                color_6 = ["#017C9D", "#D1485B", "#062530"]
                color_7 = ["#D2186D", "#880C3E", "#3A0116"]
                color_8 = ["#DC1830", "#830A12", "#340301"]

                set1 = [
                    color_1[0],
                    color_2[0],
                    color_3[0],
                    color_4[0],
                    color_5[0],
                    color_6[0],
                    color_7[0],
                    color_8[0],
                ]
                set2 = [
                    color_1[1],
                    color_2[1],
                    color_3[1],
                    color_4[1],
                    color_5[1],
                    color_6[1],
                    color_7[1],
                    color_8[1],
                ]
                set3 = [
                    color_1[2],
                    color_2[2],
                    color_3[2],
                    color_4[2],
                    color_5[2],
                    color_6[2],
                    color_7[2],
                    color_8[2],
                ]
                set1 = [rgb_to_hex(color) for color in set1]
                set2 = [rgb_to_hex(color) for color in set2]
                set3 = [rgb_to_hex(color) for color in set3]
                colors = {"set1": set1[0:n], "set2": set2[0:n], "set3": set3[0:n]}
            else:
                raise ValueError("Number of colors must be less than 9")
        return colors

    def marker_settings(self, plt_settings):

        markerfacecolor = None
        markersize = None
        if plt_settings.__contains__("marker"):
            if (plt_settings["marker"] is not None) and (
                plt_settings["marker"].__contains__("edge_color")
            ):
                markerfacecolor = plt_settings["marker"]["edge_color"]
            if plt_settings.__contains__("color"):
                markerfacecolor = plt_settings["color"]
            if plt_settings["marker"] is not None and plt_settings[
                "marker"
            ].__contains__("size"):
                markersize = plt_settings["marker"]["size"]
            else:
                markersize = 2

        marker_settings = {"markerfacecolor": markerfacecolor, "markersize": markersize}

        return marker_settings

    def add_image_to_polar_plot(self, cfg, plt_settings,plt_properties):
        if "add_image" in cfg["settings"] and cfg["settings"]["add_image"].get("flag", False):

            img_path = plt_settings['add_image']['image_path']
            transparency = plt_settings['add_image']['transperancy']
            r = plt_settings['add_image']['r']
            theta = plt_settings['add_image']['theta_center']
            
            img = Image.open(img_path)

            im_array = np.array(img.convert("RGBA"))
            im_array[:, :, 3] = (im_array[:, :, 3].astype(float) * transparency).astype(np.uint8)
    
            fig = plt_properties["fig"]
            ax = plt_properties["ax"]

            # theta_center = theta  
            theta_center = np.radians(theta)
            r_center = r 
            zoom_factor = 0.5

            image_box = OffsetImage(im_array, zoom=zoom_factor)
    
            ab = AnnotationBbox(image_box, (theta_center, r_center), frameon=False, xycoords='polar')
            
            ax.add_artist(ab)   
            #ax.set_ylim(0, 14)
    
            # plt.show() 
            #plt.savefig('docs/leg_pycodes/polar_plot_delete.png')

    def add_image_to_xy_plot(self, cfg, plt_settings):
        plt_properties = None
        if "add_image" in cfg["settings"] and cfg["settings"]["add_image"].get("flag", False):
            img_path = plt_settings['add_image']['image_path']
            transparency = plt_settings['add_image']['transperancy']
            x = plt_settings['add_image']['x']
            y = plt_settings['add_image']['y']
            img = Image.open(img_path)

            fig, ax = plt.subplots()
            # ax = plt_properties['ax']
            
            image_extent = [x['min'], x['max'], y['min'], y['max']]
            # image_extent = [-2, 1, -2, 1] 

            # Add the image to the plot
            # ax.imshow(img, extent=image_extent, alpha=transparency, zorder=-1)
            ax.imshow(img, aspect='auto', extent=image_extent, alpha=transparency, zorder=-1)

            plt_properties = {"fig": fig, "ax": ax, "plt": plt}
        else:
            print("add_image data is not available")    

        return plt_properties

    def get_plot_properties_for_df(self, cfg, df):

        plot_count_dict = self.get_plot_count_array_for_df(cfg)
        cfg["settings"]["color"] = self.get_plot_colors_for_df(plot_count_dict, cfg)
        cfg["settings"]["linestyle"] = self.get_plot_linestyle_for_df(cfg, plot_count_dict)
        cfg["settings"]["markerprops"] = self.get_plot_markerprops_for_df(cfg, plot_count_dict)
        cfg["settings"]["alpha"] = self.get_plot_alpha_for_df(cfg, plot_count_dict)

        return cfg

    def get_plot_count_array_for_df(self, cfg):

        x_count_array = []
        y_count_array = []
        plot_count_array = []
        for group_cfg in cfg["data"]["groups"]:

            if "columns" in group_cfg:
                x_count = len(group_cfg["columns"]["x"])
                y_count = len(group_cfg["columns"]["y"])
            else:
                x_count = len(group_cfg["x"])
                y_count = len(group_cfg["y"])

            x_count_array.append(x_count)
            y_count_array.append(y_count)

            plot_count_array.append(x_count * y_count)

        plot_count_dict = {
            "x_count_array": x_count_array,
            "y_count_array": y_count_array,
            "plot_count_array": plot_count_array,
        }
        return plot_count_dict

    def get_plot_colors_for_df(self, plot_count_dict, cfg, key="color"):

        x_count_array = plot_count_dict["x_count_array"]
        y_count_array = plot_count_dict["y_count_array"]
        plot_count_array = plot_count_dict["plot_count_array"]


        repeat_flag = True
        if 'pairs' in cfg['settings'] and not cfg['settings']['pairs']:
            repeat_flag = False

        if repeat_flag:
            count = plot_count_array[0]
            color_list = self.get_colors(set="single", n=count)
            color_list = color_list * len(plot_count_array)
        else:
            count = sum(plot_count_array)
            color_list = self.get_colors(set="single", n=count)

        return color_list

    def get_plot_linestyle_for_df(self, cfg, plot_count_dict, key="linestyle"):

        default_linestyle_list = ["-", "--", "-.", ":"]
        x_count_array = plot_count_dict["x_count_array"]
        y_count_array = plot_count_dict["y_count_array"]
        plot_count_array = plot_count_dict["plot_count_array"]

        repeat_flag = True
        if 'pairs' in cfg['settings'] and not cfg['settings']['pairs']:
            repeat_flag = False

        linestyle_list = []
        if repeat_flag:
            for plot_count, linestyle_item in zip(
                plot_count_array, default_linestyle_list
            ):
                linestyle_list = linestyle_list + [linestyle_item] * plot_count
        else:
            for plot_count, linestyle_item in zip(
                plot_count_array, default_linestyle_list
            ):
                linestyle_list = linestyle_list + [default_linestyle_list[0]] * plot_count

        return linestyle_list

    def get_plot_markerprops_for_df(self, cfg, plot_count_dict, key="marker"):

        default_marker_list = [
            "o",
            "v",
            "^",
            "<",
            ">",
            "8",
            "s",
            "p",
            "*",
            "h",
            "H",
            "D",
            "d",
            "P",
            "X",
        ]
        default_markersize_list = [2, 2, 2, 2]
        plot_count_array = plot_count_dict["plot_count_array"]

        repeat_flag = True
        if 'pairs' in cfg['settings'] and not cfg['settings']['pairs']:
            repeat_flag = False

        marker_list = []
        if repeat_flag:
            for plot_count, marker_item in zip(plot_count_array, default_marker_list):
                marker_list = marker_list + [marker_item] * plot_count
        else:
            for plot_count, marker_item in zip(plot_count_array, default_marker_list):
                marker_list = marker_list + [None] * plot_count

        markersize_list = []
        if repeat_flag:
            for plot_count, markersize_item in zip(
                plot_count_array, default_markersize_list
            ):
                markersize_list = markersize_list + [markersize_item] * plot_count
        else:
            for plot_count, markersize_item in zip(
                plot_count_array, default_markersize_list
            ):
                markersize_list = markersize_list + [None] * plot_count

        markerprops_list = []
        for marker, markersize in zip(marker_list, markersize_list):
            markerprops_list.append({"marker": marker, "markersize": markersize})

        return markerprops_list

    def get_plot_alpha_for_df(self, cfg, plot_count_dict, key="alpha"):

        default_alpha_list = [round(1 - n * 0.05, 2) for n in range(0, 20)]
        x_count_array = plot_count_dict["x_count_array"]
        y_count_array = plot_count_dict["y_count_array"]
        plot_count_array = plot_count_dict["plot_count_array"]

        repeat_flag = True
        if 'pairs' in cfg['settings'] and not cfg['settings']['pairs']:
            repeat_flag = False

        alpha_list = []
        if repeat_flag:
            for plot_count, alpha_item in zip(plot_count_array, default_alpha_list):
                alpha_list = alpha_list + [alpha_item] * plot_count
        else:
            for plot_count, alpha_item in zip(plot_count_array, default_alpha_list):
                alpha_list = alpha_list + [default_alpha_list[0]] * plot_count

        return alpha_list
