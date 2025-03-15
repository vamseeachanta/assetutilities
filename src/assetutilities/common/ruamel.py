import os
from ruamel.yaml import YAML

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2) 

class RuamelYaml:
    def __init__(self):
       pass

    def router(self, cfg):
        if 'yml_analysis' in cfg and cfg['yml_analysis']['divide']['flag']:
            self.divide_yaml_files(cfg)
    
    def divide_yaml_files(self, cfg):
        yml_files = cfg['file_management']['input_files']['yml']
       
        for file_name in yml_files:
            cfg_divide = cfg['yml_analysis']['divide']
            if cfg_divide['by'] == 'primary_key':
                self.divide_yaml_file_by_primary_keys(cfg, file_name)

        return cfg
    def divide_yaml_file_by_primary_keys(self, cfg, file_name):

        result_folder = cfg['Analysis']['result_folder']
       
        # Read the original YAML file
        with open(file_name) as file:
            data = yaml.load(file)
        
        output_file_name = "primary_key_clean.yml"
        output_file_path = os.path.join(result_folder, output_file_name)
        # Save it back to a new file while preserving formatting
        with open(output_file_path, "w") as f:
            yaml.dump(data, f)