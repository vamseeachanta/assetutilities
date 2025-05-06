# Reader imports
from assetutilities.common.data import AttributeDict
# from assetutilities.common.yml_utilities import WorkingWithYAML

# wwy = WorkingWithYAML()


class VisualizationTemplates:

    def __init__(self):
        pass

    def get_xy_scatter_input(self, custom_analysis_dict={}):
        library_name = 'assetutilities'
        library_yaml_cfg = {
            'filename': 'base_configs/modules/visualization/template_xy_scatter_input.yml',
            'library_name': library_name
        }
        from assetutilities.common.yml_utilities import WorkingWithYAML

        wwy = WorkingWithYAML()
        plot_template = wwy.get_library_yaml_file(library_yaml_cfg)
        plot_template['Analysis'] = custom_analysis_dict
        plot_template = AttributeDict(plot_template)

        return plot_template

    def get_xy_line_input(self, custom_analysis_dict={}):
        library_name = 'assetutilities'
        library_yaml_cfg = {
            'filename': 'base_configs/modules/visualization/template_xy_line_input.yml',
            'library_name': library_name
        }
        from assetutilities.common.yml_utilities import WorkingWithYAML
        wwy = WorkingWithYAML()
        plot_template = wwy.get_library_yaml_file(library_yaml_cfg)
        plot_template['Analysis'] = custom_analysis_dict
        plot_template = AttributeDict(plot_template)

        return plot_template

    def get_xy_scatter_csv(self, custom_analysis_dict={}):
        library_name = 'assetutilities'
        library_yaml_cfg = {
            'filename': 'base_configs/modules/visualization/template_xy_scatter_csv.yml',
            'library_name': library_name
        }
        from assetutilities.common.yml_utilities import WorkingWithYAML
        wwy = WorkingWithYAML()
        plot_template = wwy.get_library_yaml_file(library_yaml_cfg)
        plot_template['Analysis'] = custom_analysis_dict
        plot_template = AttributeDict(plot_template)

        return plot_template

    def get_xy_line_csv(self, custom_analysis_dict={}):
        library_name = 'assetutilities'
        library_yaml_cfg = {
            'filename': 'base_configs/modules/visualization/template_xy_line_csv.yml',
            'library_name': library_name
        }
        from assetutilities.common.yml_utilities import WorkingWithYAML
        wwy = WorkingWithYAML()
        plot_template = wwy.get_library_yaml_file(library_yaml_cfg)
        plot_template['Analysis'] = custom_analysis_dict
        plot_template = AttributeDict(plot_template)

        return plot_template
    
    def get_x_datetime_input_matplotlib(self, custom_analysis_dict={}):
        library_name = 'assetutilities'
        library_yaml_cfg = {
            'filename': 'base_configs/modules/visualization/template_x_datetime_matplotlib.yml',
            'library_name': library_name
        }
        from assetutilities.common.yml_utilities import WorkingWithYAML
        wwy = WorkingWithYAML()
        plot_template = wwy.get_library_yaml_file(library_yaml_cfg)
        plot_template['Analysis'] = custom_analysis_dict
        plot_template = AttributeDict(plot_template)

        return plot_template
