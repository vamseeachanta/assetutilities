import logging

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt


class VisualizationComponents():
    # https://plot.ly/python/v3/fft-filters/
    # http://scipy-lectures.org/intro/scipy/auto_examples/plot_fftpack.html
    # https://dsp.stackexchange.com/questions/724/low-pass-filter-and-fft-for-beginners-with-python

    def __init__(self, cfg=None):
        self.cfg = cfg

    def visualization_router(self, cfg):
        #TODO program to handle multiple plots with a single input file. Architecture exists but refinement needed with tests.
        plt_settings = cfg['settings']
        if 'polar' in cfg['settings']['plt_kind']:
            data_df = self.get_polar_data(cfg)
            plt_settings['traces'] = int(len(data_df.columns) / 2)
            if cfg['settings']['plt_engine'] == 'plotly':
                plt = self.get_polar_plot_plotly(data_df, plt_settings)
                self.save_polar_plot_and_close_plotly(plt, cfg)
            elif cfg['settings']['plt_engine'] == 'matplotlib':
                plt_properties = self.get_polar_plot_matplotlib(
                    data_df, plt_settings, cfg)
                self.save_polar_plot_and_close_matplotlib(plt_properties, cfg)
        else:
            raise (Exception(f'Other plots coding to be completed ... FAIL'))

    def get_polar_data(self, cfg):
        data_dict = self.get_polar_mapped_data_dict(cfg)
        data_df = pd.DataFrame.from_dict(data_dict, orient='index').transpose()
        return data_df

    def get_polar_mapped_data_dict(self, cfg):
        theta_data = cfg['data']['theta']
        r_data = cfg['data']['r']

        # Get legend data
        if 'legend' in cfg['data']:
            legend_data = cfg['data']['legend']
        else:
            legend_data = []

        no_of_trends = max(len(theta_data), len(r_data))
        if not len(legend_data) == no_of_trends:
            legend_data = ['legend_' + str(i) for i in range(0, no_of_trends)]

        if len(theta_data) < len(r_data):
            theta_data = [theta_data[0]] * len(r_data)
        if len(theta_data) > len(r_data):
            r_data = [r_data[0]] * len(theta_data)

        for theta_index in range(0, len(theta_data)):
            new_data = [
                theta * np.pi / 180 for theta in theta_data[theta_index]
            ]
            theta_data[theta_index] = new_data

        data_dict = {}
        for i in range(0, len(legend_data)):
            data_dict.update({'r_' + str(i): r_data[i]})
            data_dict.update({'theta_' + str(i): theta_data[i]})

        return data_dict

    def get_axis_for_polar(self, rect):
        rect_polar = rect.copy()
        rect_polar[0] = rect[0] * np.pi / 180
        rect_polar[1] = rect[1] * np.pi / 180

        return rect_polar

    def get_raw_data(self):
        if self.cfg.default['input_data']['source'] == 'db':
            self.get_environments()
            for env_index in range(0, len(self.environments)):
                # for env_index in range(0, 1):
                self.env = self.environments[env_index]
                db_properties = self.cfg.default['db'][self.env]
                self.set_up_db_connection(db_properties)
                try:
                    self.get_input_data()
                except Exception as e:
                    print("Error encountered: {}".format(e))
                    logging.info(str(e))
                    print("No connection to environment {}".format(self.env))
        else:
            import sys
            print("No data source specified")
            sys.exit()

    def get_input_data(self):
        cfg_input = self.cfg.default['input_data'].copy()
        if cfg_input['source'] == 'db':
            self.dbe.get_input_data_from_db(cfg_input)
        else:
            print("No input data source defined")

    def get_environments(self):
        self.environments = list(self.cfg.default['db'].keys())

    def set_up_db_connection(self, db_properties):
        from common.database import Database
        self.dbe = Database(db_properties)
        try:
            self.dbe.enable_connection_and_cursor()
            return True
        except Exception as e:
            print("Error as {}".format(e))
            print("No connection for environment: {}".format(db_properties))
            return False

    def save_raw_data(self):
        if self.cfg.default['input_data'].__contains__(
                'save') and self.cfg.default['input_data']['save']['flag']:
            from common.data import SaveData
            save_data = SaveData()
            cfg_input = self.cfg.default['input_data'].copy()
            sheet_array = []
            df_array = []
            for set_index in range(0, len(cfg_input['sets'])):
                set_info = cfg_input['sets'][set_index]
                sheet_array.append(set_info['label'])
                df = getattr(self.dbe, 'input_data_' + set_info['label'])
                if cfg_input['save']['to_csv']:
                    file_name = self.cfg['Analysis'][
                        'result_folder'] + self.cfg['Analysis'][
                            'file_name'] + '_' + sheet_array[set_index] + '.csv'
                    df.to_csv(file_name, index=False)
                df_array.append(df)

            if cfg_input['save']['to_xlsx']:
                cfg_temp = {
                    'SheetNames':
                        sheet_array,
                    'FileName':
                        self.cfg['Analysis']['result_folder'] +
                        self.cfg['Analysis']['file_name'] + '.xlsx'
                }
                save_data.DataFrameArray_To_xlsx_openpyxl(df_array, cfg_temp)

    def prepare_visualizations(self, app_object=None):
        if self.cfg.__contains__('plot_settings'):
            self.prepare_single()
        if self.cfg.__contains__('plot_multiple'):
            self.prepare_multiple(app_object)

    def prepare_single(self):
        from assetutilities.common.visualizations import Visualization
        viz_data = Visualization()

        for plt_index in range(0, len(self.cfg['plot_settings'])):
            plt_settings = self.cfg['plot_settings'][plt_index]
            df = self.prepare_plot_input_data(plt_index, plt_settings)

            plt_settings.update({
                'file_name':
                    self.cfg['Analysis']['result_folder'] +
                    self.cfg['Analysis']['file_name'] + '_' +
                    plt_settings['file_name_extension'] + '.png'
            })

            for data_index in range(0, len(plt_settings['data'])):
                plt_settings_temp = plt_settings['data'][data_index].copy()
                viz_data.from_df_columns(df, plt_settings_temp)

            viz_data.add_title_and_axis_labels()
            viz_data.add_legend()
            viz_data.add_x_y_lim_formats()
            viz_data.add_reference_lines_and_spans()
            viz_data.save_and_close()

    def prepare_plot_input_data(self, data_set_cfg, app_object=None):
        if data_set_cfg['df'] == 'input_data_table_statistics':
            df = self.dbe.prepare_input_statistics(data_set_cfg)
        elif app_object is None:
            df = getattr(self.dbe, data_set_cfg['df'])
        else:
            if 'output' in data_set_cfg['df']:
                df = getattr(app_object, data_set_cfg['df'])
            elif 'input_data_' in data_set_cfg['df']:
                if hasattr(app_object, 'dbe'):
                    df = getattr(app_object.dbe, data_set_cfg['df'])
                elif hasattr(app_object, data_set_cfg['df']):
                    df = getattr(app_object, data_set_cfg['df'])
            else:
                import pandas as pd
                print(
                    "Data frame with label: {} can not be found in class object"
                    .format(data_set_cfg['df']))
                df = pd.DataFrame()

        df = self.get_filtered_df(data_set_cfg, df)
        df = self.get_scaled_df(data_set_cfg, df)

        return df

    def get_filtered_df(self, data_set_cfg, df):
        from common.data import ReadData
        read_data = ReadData()
        df = df.copy()
        if data_set_cfg.__contains__('filter'):
            df = read_data.df_filter_by_column_values(data_set_cfg.copy(), df)
        return df.copy()

    def get_scaled_df(self, data_set_cfg, df):
        df = df.copy()
        if data_set_cfg.__contains__('scale'):
            for column_index in range(0, len(data_set_cfg['scale']['columns'])):
                column_name = data_set_cfg['scale']['columns'][column_index]
                df[column_name] = df[column_name] * data_set_cfg['scale'][
                    'factors'][column_index]
        return df

    def prepare_multiple(self, app_object):
        from common.visualizations import Visualization
        self.viz_data = Visualization()

        for mult_plt_index in range(0, len(self.cfg['plot_multiple'])):
            self.prepare_a_multiple_plot(mult_plt_index, app_object)

    def prepare_a_multiple_plot(self, mult_plt_index, app_object=None):
        cfg_mult = self.cfg['plot_multiple'][mult_plt_index].copy()
        if cfg_mult.__contains__('nrows'):
            nrows = cfg_mult['nrows']
        else:
            nrows = len(cfg_mult['sets'])
        if cfg_mult.__contains__('ncols'):
            ncols = cfg_mult['ncols']
        else:
            ncols = 1

        if cfg_mult['file_name_extension'] is not None:
            cfg_mult.update({
                'file_name':
                    self.cfg['Analysis']['result_folder'] +
                    self.cfg['Analysis']['file_name'] + '_' +
                    cfg_mult['file_name_extension'] + '.png'
            })
        else:
            cfg_mult.update({
                'file_name':
                    self.cfg['Analysis']['result_folder'] +
                    self.cfg['Analysis']['file_name'] + '.png'
            })
        self.viz_data.multiple_plots(cfg_mult)
        for plt_index in range(0, nrows * ncols):
            plt_settings = cfg_mult['sets'][plt_index]
            self.viz_data.autoselect_current_subplot(plt_index)
            if not plt_settings.__contains__('data'):
                self.plotting_for_no_data_object(plt_settings, app_object)
            else:
                for data_set_index in range(0, len(plt_settings['data'])):
                    data_set_cfg = plt_settings['data'][data_set_index]
                    self.plot_a_data_set(app_object, data_set_cfg)

            self.viz_data.add_title_and_axis_labels(plt_settings)
            self.viz_data.add_x_y_lim_formats()
            self.viz_data.resolution_adjust()
            self.viz_data.add_reference_lines_and_spans()
        self.viz_data.save_and_close()

    def plot_a_data_set(self, app_object, data_set_cfg):
        try:
            df = self.prepare_plot_input_data(data_set_cfg, app_object)
            if len(df) > 0:
                if data_set_cfg['x'].__contains__('fft_freq'):
                    if data_set_cfg.__contains__('color'):
                        color = data_set_cfg['color']
                    else:
                        color = None
                    cfg_text = self.add_fft_peaks_notes(df, color)
                    data_set_cfg.update(cfg_text)
                self.viz_data.plot_subplot(df, data_set_cfg)
                self.viz_data.add_legend()
                self.viz_data.add_text_fields()
        except Exception as e:
            print("See Error below. Can not process {}. ".format(
                str(data_set_cfg)))
            print("Error: {}".format(e))

    def plotting_for_no_data_object(self, plt_settings, app_object):
        if plt_settings['df_array']['flag']:
            df_array_label = plt_settings['df_array']['variable']
            df_array_dict = getattr(app_object, df_array_label)
            df_labels = list(df_array_dict.keys())
            for data_set_index in range(0, len(df_labels)):
                data_set_cfg = plt_settings['df_array'].copy()
                label = df_labels[data_set_index]
                data_set_cfg.update({'label': [label]})
                app_object.output_df_temp_from_df_array = df_array_dict[label]
                self.plot_a_data_set(app_object, data_set_cfg)
        else:
            import sys
            print(
                "Could not find data object. So exiting application without plotting"
            )
            sys.exit()

    def add_fft_peaks_notes(self, df, color=None):
        notes_array = []
        notes_df = df[df['peak_flag'] == True].copy()
        notes_df.reset_index(inplace=True, drop=True)
        for notes_index in range(0, len(notes_df)):
            x = notes_df['fft_freq'].iloc[notes_index]
            y = notes_df['power'].iloc[notes_index]
            notes_element = {
                'x': x,
                'y': y,
                'text': ' {0} s, {1} Hz'.format(round(1 / x, 2), round(x, 2))
            }
            notes_element.update({'color': color})
            notes_array.append(notes_element)

        cfg_text = {'text_fields': notes_array}
        return cfg_text

    def run_example(self):
        pass
        # TBA

    def get_polar_plot_plotly(self, df, plt_settings):
        if plt_settings['plt_kind'] == 'polar':
            # Radial line

            plt.polar(df['x'], df['y'], label=plt_settings['label'])
        elif plt_settings['plt_kind'] == 'polar_scatter':
            # Radial scatter
            import plotly.express as px
            plt = px.scatter_polar(df, r=df['r_0'], theta=df['theta_0'])

        return plt

    def get_polar_plot_matplotlib(self, df, plt_settings, cfg):

        import matplotlib.pyplot as plt
        if 'plt_properties' in plt_settings and plt_settings['plt_properties'][
                'plt'] is not None:
            plt = plt_settings['plt_properties']['plt']

        # Add axis for plot

        alpha = plt_settings.get('alpha', 1)
        facecolor = plt_settings.get('facecolor', None)
        if (not 'add_axes' in plt_settings) or (not plt_settings['add_axes']):
            fig, ax = plt.subplots(subplot_kw={'projection': 'polar'},
                                   facecolor=facecolor,
                                   alpha=alpha)
        else:
            fig = plt_settings['plt_properties']['fig']
            rect = plt_settings['rect']
            ax = fig.add_axes(rect,
                              polar=True,
                              facecolor=facecolor,
                              alpha=alpha)

            axis = plt_settings['axis']
            if axis != 'off':
                axis = self.get_axis_for_polar(axis)
            plt.axis(axis)

        # Add trace or plot style
        for index in range(0, plt_settings['traces']):
            if plt_settings['plt_kind'][index] == 'polar':
                ax.plot(df['theta_' + str(index)],
                        df['r_' + str(index)],
                        label=plt_settings['legend']['label'][index],
                        color=cfg['data']['color'][index],
                        linestyle=cfg['data']['linestyle'][index],
                        alpha=cfg['data']['alpha'][index])
            elif plt_settings['plt_kind'][index] == 'polar_scatter':
                ax.scatter(df['theta_' + str(index)],
                           df['r_' + str(index)],
                           label=plt_settings['legend']['label'][index],
                           color=cfg['data']['color'][index],
                           linestyle=cfg['data']['linestyle'][index],
                           alpha=cfg['data']['alpha'][index])

        legend_flag = plt_settings['legend'].get('flag', True)
        if legend_flag:
            ax.legend(loc='best')
            prop = plt_settings['legend'].get('prop', None)
            if prop is not None:
                plt.legend(prop=prop)
            # ax.legend(bbox_to_anchor=(1.04, 0.5),
            #           loc="center left",
            #           borderaxespad=0)
            # ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left",
            #                 mode="expand", borderaxespad=0, ncol=3)

        plt = self.get_plt_with_arrows(plt, plt_settings)

        set_rmax = plt_settings.get('set_rmax', None)
        if set_rmax is not None:
            ax.set_rmax(set_rmax)

        set_rticks = plt_settings.get('set_rticks', None)
        if set_rticks is not None:
            ax.set_rticks(set_rticks)

        set_rlabel_position = plt_settings.get('set_rlabel_position', None)
        if set_rlabel_position is not None:
            ax.set_rlabel_position(set_rlabel_position)

        set_thetagrids = plt_settings.get('set_thetagrids', None)
        if set_thetagrids is not None:
            ax.set_thetagrids(set_thetagrids)

        set_theta_zero_location = plt_settings.get('set_theta_zero_location',
                                                   None)
        if set_theta_zero_location is not None:
            ax.set_theta_zero_location(set_theta_zero_location)

        grid = plt_settings.get('grid', True)
        ax.grid(grid)

        title = plt_settings.get('title', None)
        if title is not None:
            ax.set_title(plt_settings['title'], va='bottom')

        plt_properties = {'plt': plt, 'fig': fig}
        if 'add_axes' in cfg and len(cfg.add_axes) > 0:
            self.add_axes_to_plt(plt_properties, cfg)

        return {'plt': plt, 'fig': fig}

    def add_axes_to_plt(self, plt_properties, cfg):
        for axes_idx in range(0, len(cfg.add_axes)):
            cfg_plt = cfg.add_axes[axes_idx]
            plt_settings = cfg_plt['settings']
            plt_settings.update({'add_axes': True})
            plt_settings.update({'plt_properties': plt_properties})

            data_df = self.get_polar_data(cfg_plt)
            plt_settings['traces'] = int(len(data_df.columns) / 2)

            plt = self.get_polar_plot_matplotlib(data_df, plt_settings, cfg_plt)

    def get_plt_with_arrows(self, plt, plt_settings):

        # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.arrow.html
        # Add arrows with direct data
        # Try inset_axes: https://matplotlib.org/2.0.2/examples/pylab_examples/axes_demo.html
        if not 'arrows' in plt_settings:
            return plt

        arrows = plt_settings['arrows']
        for arrow in arrows:
            # arr1 = plt.arrow(3, 0, 5, 45, color='blue')
            # # arrow at 45 degree
            theta = arrow['theta']
            r = arrow['r']
            color = arrow['color']

            arr = plt.arrow(theta[0] / 180. * np.pi,
                            r[0],
                            theta[1] / 180. * np.pi,
                            r[1] - r[0],
                            alpha=0.75,
                            width=0.015,
                            color=color,
                            lw=2,
                            zorder=5)

        return plt

    def save_plot(self, plt, plt_settings):
        file_name = plt_settings['file_name']
        if plt_settings['multiple']:
            self.fig.savefig(file_name, dpi=500)
        else:
            try:
                self.plt.savefig(file_name, dpi=800)
            except:
                self.plt.savefig(file_name, dpi=100)
            self.plt.close()

    def save_polar_plot_and_close_plotly(self, plt, cfg):
        plot_name_paths = self.get_plot_name_path(cfg)
        for file_name in plot_name_paths:
            # plt.write_image(file_name)
            plt.write_html(file_name)

            plt.savefig(file_name, dpi=100)

        plt.close()

    def save_polar_plot_and_close_matplotlib(self, plt_properties, cfg):
        plot_name_paths = self.get_plot_name_path(cfg)

        plt = plt_properties['plt']
        for file_name in plot_name_paths:
            plt.savefig(file_name, dpi=800)

    def get_plot_name_path(self, cfg):
        file_name = cfg['settings']['file_name']
        extensions = cfg['settings']['plt_save_extensions']
        plot_name_paths = [
            cfg['Analysis']['result_folder'] + 'Plot\\' + file_name + extension
            for extension in extensions
        ]

        return plot_name_paths

    def add_annotations(self):
        '''
        https://matplotlib.org/stable/gallery/text_labels_and_annotations/annotation_demo.html
        #TODO abstract annotation and move to another function.
        or use graphics?
        '''
        ax.annotate(
            'a polar annotation',
            xy=(30, 5),    # theta, radius
            xytext=(0.05, 0.05),    # fraction, fraction
            textcoords='figure fraction',
            arrowprops=dict(facecolor='black', shrink=0.05),
            horizontalalignment='left',
            verticalalignment='bottom')
