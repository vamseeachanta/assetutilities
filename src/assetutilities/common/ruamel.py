import os
import re
from ruamel.yaml import YAML
from loguru import logger

yaml = YAML()
yaml.preserve_quotes = True  # Keeps quotes if present 
yaml.allow_duplicate_keys = True  # Allows duplicate keys in the YAML file
yaml.indent(mapping=2, sequence=4, offset=2) 

from pathlib import Path

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
                logger.debug("Splitting primary keys data START...")
                self.divide_yaml_file_by_primary_keys(cfg, file_name)

        return cfg 
    def divide_yaml_file_by_primary_keys(self, cfg, file_name):
        result_folder = cfg['Analysis']['result_folder']
        file_name_stem = Path(file_name).stem
        
        with open(file_name, "r", encoding='utf-8-sig') as file:
            yaml_content = file.read()
            
            cleaned_yaml = self.clean_yaml_file(yaml_content)
            cleaned_yaml = self.extract_data_after_document_start(cleaned_yaml)
            
            data = yaml.load(cleaned_yaml)
        
        primary_key_patterns = []
        for line in cleaned_yaml.splitlines():
            # Match primary key definitions (key: value)
            match = re.match(r'^(\s*)([^:]+)\s*:', line)
            if match:
                #indent = match.group(1)
                key = match.group(2).strip()
                # Check if the rest of the line contains the value (single-line)
                value_part = line[match.end():].strip()
                if value_part:  # If there's content after the colon
                    primary_key_patterns.append((key, True))  # True = single line
                else:
                    primary_key_patterns.append((key, False))  # False = multi-line
        
        # Convert to dictionary for easy lookup
        is_single_line = {key: single for key, single in primary_key_patterns}
        
        # Process each primary key
        for key in data.keys():
            # Skip if the key is marked as single-line in the original YAML
            if is_single_line.get(key, False):
                continue
                
            output_file_name = f"{file_name_stem}_{key}.yml"
            output_file_path = os.path.join(result_folder, output_file_name)
            
            with open(output_file_path, "w", encoding='utf-8-sig') as f:
                yaml.dump({key: data[key]}, f)
            logger.debug("Splitting primary keys data END...")
            

    
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

    def extract_data_after_document_start(self, yaml_content):
        """
        Extracts the YAML content after the document start symbol (---).
        """
        # Split the content by the document start symbol
        parts = yaml_content.split('---', 1)
        if len(parts) > 1:
            return parts[1].strip()  # Return the content after '---'
        return yaml_content  # If '---' is not found, return the entire content
