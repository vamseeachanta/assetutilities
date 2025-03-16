import os
import re
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True  # Keeps quotes if present 
yaml.allow_duplicate_keys = True  # Allows duplicate keys in the YAML file
yaml.indent(mapping=2, sequence=4, offset=2) 

class RuamelYaml:
    def __init__(self):
       pass

    def router(self, cfg):
        if 'yml_analysis' in cfg and cfg['yml_analysis']['divide']['flag']:
            self.divide_yaml_files(cfg)
        return cfg
    
    def divide_yaml_files(self, cfg):
        yml_files = cfg['file_management']['input_files']['yml']
       
        for file_name in yml_files:
            cfg_divide = cfg['yml_analysis']['divide']
            if cfg_divide['by'] == 'primary_key':
                self.divide_yaml_file_by_primary_keys(cfg, file_name)

        return cfg
    def divide_yaml_file_by_primary_keys(self, cfg, file_name):

        result_folder = cfg['Analysis']['result_folder']
       
        with open(file_name, "r", encoding='utf-8-sig') as file:
            yaml_content = file.read()
            
            # Clean the YAML content
            cleaned_yaml = self.clean_yaml_file(yaml_content)
            
            data = yaml.load(file)
        
        output_file_name = "primary_key_output.yml"
        output_file_path = os.path.join(result_folder, output_file_name)
        
        with open(output_file_path, "w",encoding='utf-8-sig') as f:
            yaml.dump(data, f)
    
    def clean_yaml_line(self,line):
        """
        Cleans a single line of YAML by removing invalid tokens or characters.
        """
        if '%' in line:
            line = re.sub(r'(\s*[^:]+:\s*)%([^%]+)%', r'\1"\2"', line)  # Wrap %...% in quotes
        return line

    def clean_yaml_file(self,yaml_content):
        """
        Cleans the entire YAML content by removing invalid lines and tokens.
        """
        cleaned_lines = []
        for line in yaml_content.splitlines():
            cleaned_line = self.clean_yaml_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return '\n'.join(cleaned_lines)