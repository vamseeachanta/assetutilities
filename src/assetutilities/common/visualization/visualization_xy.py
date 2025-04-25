# Standard library imports
from loguru import logger
import math
from datetime import datetime, timedelta

# Third party imports
import matplotlib.pyplot as plt  # noqa
import plotly.io as pio  # noqa
import pandas as pd  # noqa
from colorama import Fore, Style
from colorama import init as colorama_init

# Reader imports
from assetutilities.common.data_management import DataManagement
from assetutilities.common.utilities import is_file_valid_func
from assetutilities.common.visualization.visualization_common import VisualizationCommon

colorama_init()
dm = DataManagement()
visualization_common = VisualizationCommon()


class VisualizationXY:

    def __init__(self):
        pass

    def xy_plot_set_up_and_save(self, cfg, plt_settings):
        data_df, cfg = self.get_data_df_and_plot_properties(cfg)
        if cfg['settings']['plt_engine'] == 'plotly':
            fig = self.get_xy_plot_plotly(data_df, plt_settings,cfg)
            self.save_xy_plot_and_close_plotly(fig, cfg)
        elif cfg["settings"]["plt_engine"] == "matplotlib":
            plt_properties = visualization_common.add_image_to_xy_plot(cfg, plt_settings)
            plt_properties = self.get_xy_plot_matplotlib(data_df, plt_settings, cfg, plt_properties)
            self.save_xy_plot_and_close_matplotlib(cfg)
        else:
            raise ValueError("Invalid plt_engine")

    def get_data_df_and_plot_properties(self, cfg):
        if cfg["data"]["type"] == "input":
            data_dict, legend = self.get_xy_mapped_data_dict_from_input(cfg)
            if len(cfg["settings"]["legend"]["label"]) == 0:
                cfg["settings"]["legend"]["label"] = legend

        elif cfg["data"]["type"] == "csv":
            data_dict, cfg = self.get_xy_mapped_data_dict_from_csv(cfg)
        data_df = pd.DataFrame.from_dict(data_dict, orient="index").transpose()

        cfg = visualization_common.get_plot_properties_for_df(cfg, data_df)

        return data_df, cfg

    def get_xy_mapped_data_dict_from_input(self, mapped_data_cfg):
        data_dict = {}
        legend = []
        trace_count = 0
        
        for group_cfg in mapped_data_cfg["data"]['groups']:
            x_data = group_cfg["x"]
            if len(x_data[0]) == 0 and "x_datetime" in mapped_data_cfg['settings']['plt_model']:
                self.add_sample_dates_to_x_data(group_cfg)
            x_data = group_cfg["x"]
            y_data = group_cfg["y"]
            length_x = len(x_data[0])
            length_y = len(y_data[0])
            # equal the length of x and y data
            if length_x != length_y:
                min_length = min(length_x, length_y)
                x_data = [x[:min_length] for x in x_data]
                y_data = [y[:min_length] for y in y_data]
                
            legend_item = group_cfg.get("label", None)
            legend.append(legend_item if legend_item else f"Series {len(legend) + 1}")

            # Ensure both x and y have the same length
            no_of_trends = max(len(x_data), len(y_data))

            if len(x_data) < len(y_data):
                x_data = [x_data[0]] * len(y_data)
            if len(x_data) > len(y_data):
                y_data = [y_data[0]] * len(x_data)

            for i in range(0, no_of_trends):
                data_dict.update({"x_" + str(i+trace_count): x_data[i]})
                data_dict.update({"y_" + str(i+trace_count): y_data[i]})
            trace_count += no_of_trends

        return data_dict, legend
    
    def add_sample_dates_to_x_data(self, group_cfg):
        '''
        Add sample dates to x data for test
        '''
        start_time = datetime(2024,8,1)
        end_time = datetime.now()
        dates = group_cfg['x'][0]
        current = start_time
        while current <= end_time:
            dates.append(current)
            current += timedelta(days=32)
        group_cfg["x"] = [dates]
        return group_cfg

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
                logger.error(FileNotFoundError(f'Invalid file name/path: {group_cfg["file_name"]}'))
                logger.error(f'Please check the file name/path in the input file: {group_cfg["file_name"]}' )
                logger.error(f'Program {Fore.RED}continues to run ...{Style.RESET_ALL}')

            else:
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
            logger.info("Using legend labels from the input file")
        elif len(cfg["settings"]["legend"]["label"]) > 0:
            logger.warning(
                "The number of legend labels is not equal to the number of data columns."
            )
            logger.warning("Ignoring the legend labels in the input file")

        mapped_data_cfg = {"data": {"groups": [{"x": x_data_array, "y": y_data_array}]}}
        cfg["settings"]["legend"]["label"] = legend_data
        data_dict, legend_unused = self.get_xy_mapped_data_dict_from_input(mapped_data_cfg)

        return data_dict, cfg

    def get_xy_plot_matplotlib(self, df, plt_settings, cfg, plt_properties):
        if plt_properties != None:
            plt = plt_properties["plt"]
            fig = plt_properties["fig"]
            ax = plt_properties["ax"]
        else:
            # Third party imports
            import matplotlib.pyplot as plt  # noqa
            fig, ax = plt.subplots()
            plt_properties = {"plt": plt, "fig": fig, 'ax': ax}

        if (
            "plt_properties" in plt_settings
            and plt_settings["plt_properties"]["plt"] is not None
        ):
            plt = plt_settings["plt_properties"]["plt"]


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

            label = None
            if (isinstance(plt_settings["legend"]["label"], list) and len(plt_settings["legend"]["label"]) > index):
                label = plt_settings["legend"]["label"][index]

            if "line" in plot_mode and "scatter" in plot_mode:
                ax.plot(
                    df["x_" + str(index)],
                    df["y_" + str(index)],
                    label=label,
                    alpha=alpha_list[index],
                    **marker_style,
                )
            elif "line" in plot_mode:
                ax.plot(
                    df["x_" + str(index)],
                    df["y_" + str(index)],
                    label= label,
                    color=color_list[index],
                    linestyle=linestyle_list[index],
                    alpha=alpha_list[index],
                )

            elif "scatter" in plot_mode:
                ax.scatter(
                    df["x_" + str(index)],
                    df["y_" + str(index)],
                    label=label,
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
            visualization_common.add_axes_to_plt(plt_properties, cfg)

        ax.set(
            xlabel=plt_settings.get("xlabel", None),
            ylabel=plt_settings.get("ylabel", None),
        )
        ax.label_outer()

        plt = visualization_common.add_x_y_lim_formats(cfg, plt) 

        # Third party imports
        import matplotlib.dates as mdates  # noqa

        if "plt_model" in cfg['settings'] and cfg['settings']['plt_model'] == "x_datetime":
            locator = cfg['settings'].get("locator", None)
            locator_map = {
                "monthly": (mdates.MonthLocator(interval=1), mdates.DateFormatter("%b %Y")),
                "daily": (mdates.DayLocator(interval=2), mdates.DateFormatter("%d %b %Y")),
                "weekly": (mdates.WeekdayLocator(interval=1), mdates.DateFormatter("%d %b %Y")),
                "yearly": (mdates.YearLocator(), mdates.DateFormatter("%Y"))
            }

            loc, fmt = locator_map.get(locator,locator_map[locator])
            ax.xaxis.set_major_locator(loc)
            ax.xaxis.set_major_formatter(fmt)

            plt.xticks(rotation=45) # rotates x-axis labels
            fig.autofmt_xdate() # auto formats x-axis date
               

        plt_properties = {"plt": plt, "fig": fig, 'ax': ax}
        return plt_properties
    
    def get_xy_plot_plotly(self, df, plt_settings, cfg):
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Create figure
        fig = go.Figure()
        
        # Get plot settings
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
        
        # Mapping from matplotlib linestyle to plotly dash style
        line_style_map = {
            '-': 'solid',
            '--': 'dash',
            ':': 'dot',
            '-.': 'dashdot',
            'solid': 'solid',
            'dashed': 'dash',
            'dotted': 'dot',
            'dashdot': 'dashdot'
        }
        # Add traces
        for index in range(0, plt_settings["traces"]):
            label = None
            if (isinstance(plt_settings["legend"]["label"], list) and len(plt_settings["legend"]["label"]) > index):
                label = plt_settings["legend"]["label"][index]
            
            x_data = df["x_" + str(index)]
            y_data = df["y_" + str(index)]
            
            # Convert matplotlib linestyle to plotly dash style
            line_style = linestyle_list[index]
            plotly_dash = line_style_map.get(line_style, 'solid')
            if "line" in plot_mode and "scatter" in plot_mode:
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=label,
                    mode='lines+markers',
                    line=dict(
                        color=color_list[index],
                        dash=plotly_dash,
                    ),
                    marker=dict(
                        symbol=markerprops_list[index]["marker"],
                        size=markerprops_list[index]["markersize"],
                        color=color_list[index],
                        line=dict(width=0)
                    ),
                    opacity=alpha_list[index]
                ))
            elif "line" in plot_mode:
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=label,
                    mode='lines',
                    line=dict(
                        color=color_list[index],
                        dash=plotly_dash,
                    ),
                    opacity=alpha_list[index]
                ))
            elif "scatter" in plot_mode:
                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    name=label,
                    mode='markers',
                    marker=dict(
                        symbol=markerprops_list[index]["marker"],
                        size=markerprops_list[index]["markersize"],
                        color=color_list[index],
                        line=dict(width=0)
                    ),
                    opacity=alpha_list[index]
                ))
        
        # Set titles and labels
        title = plt_settings.get("title", None)
        if title is not None:
            fig.update_layout(title=title)
        
        suptitle = plt_settings.get("suptitle", None)
        if suptitle is not None:
            fig.update_layout(title_text=suptitle, title_y=0.98)
        
        fig.update_layout(
            xaxis_title=plt_settings.get("xlabel", None),
            yaxis_title=plt_settings.get("ylabel", None),
            showlegend=plt_settings.get("legend", {}).get("flag", True)
        )
        
        # Handle legend
        legend_settings = plt_settings.get("legend", None)
        if legend_settings and legend_settings.get("flag", True):
            loc = legend_settings.get("loc", "best")
            # Map matplotlib legend locations to plotly
            loc_mapping = {
                "best": None,
                "upper right": "top right",
                "upper left": "top left",
                "lower left": "bottom left",
                "lower right": "bottom right",
                "right": "right",
                "center left": "left",
                "center right": "right",
                "lower center": "bottom",
                "upper center": "top",
                "center": "center"
            }
            legend_loc = loc_mapping.get(loc, None)
            fig.update_layout(legend=dict(
                orientation="h" if loc in ["upper center", "lower center", "center"] else "v",
                yanchor="auto",
                xanchor="auto",
                x=0.5 if loc in ["upper center", "lower center", "center"] else None,
                y=1.1 if loc == "upper center" else -0.2 if loc == "lower center" else None
            ))
        
        # Handle grid
        grid = plt_settings.get("grid", True)
        fig.update_layout(
            xaxis=dict(showgrid=grid),
            yaxis=dict(showgrid=grid)
        )
        
        # Handle date formatting
        if "plt_model" in cfg['settings'] and cfg['settings']['plt_model'] == "x_datetime":
            locator = cfg['settings'].get("locator", None)
            locator_map = {
                "monthly": "%b %Y",
                "daily": "%d %b %Y",
                "weekly": "%d %b %Y",
                "yearly": "%Y"
            }
            date_format = locator_map.get(locator, "%b %Y")
            fig.update_layout(
                xaxis=dict(
                    tickformat=date_format
                )
            )
        
        # Handle axes limits
        if 'xlim' in cfg['settings']:
            fig.update_xaxes(range=cfg['settings']['xlim'])
        if 'ylim' in cfg['settings']:
            fig.update_yaxes(range=cfg['settings']['ylim'])
        
        return fig
    
    def save_xy_plot_and_close_plotly(self, fig, cfg):
    
        plot_name_paths = visualization_common.get_plot_name_path(cfg)
        for file_path in plot_name_paths:
            pio.write_image(fig, file_path) 

    def save_xy_plot_and_close_matplotlib(self,  cfg):
        plot_name_paths = visualization_common.get_plot_name_path(cfg)
        for file_name in plot_name_paths:
            plt.savefig(file_name, dpi=800)

        plt.close()

    def resolve_legends(self):
        pass
        # TODO Resolve legends in a comprehensive manner
        # Get legend data
        # if "legend" in mapped_data_cfg["data"]:
        #     legend_data = mapped_data_cfg["data"]["legend"]
        # elif "legend_data" in mapped_data_cfg:
        #     legend_data = mapped_data_cfg["legend_data"]
        # else:
        #     legend_data = []

        # no_of_trends = max(len(x_data), len(y_data))

        # if not len(legend_data) == no_of_trends:
        #     legend_data = ["legend_" + str(i) for i in range(0, no_of_trends)]

