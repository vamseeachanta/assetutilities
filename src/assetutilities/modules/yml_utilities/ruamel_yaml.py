from ruamel.yaml import YAML as ruamelYAML
from pathlib import Path
from loguru import logger

import os
import re
#from ruamel.yaml.comments import CommentedMap

ruamel_yaml = ruamelYAML()
ruamel_yaml.preserve_quotes = True  # Keeps quotes if present 
ruamel_yaml.allow_duplicate_keys = True  # Allows duplicate keys if required
ruamel_yaml.indent(mapping=2, sequence=4, offset=2) 


class RuamelYAML:

    def __init__(self):
        pass

    def router(self, cfg):
        if 'yml_analysis' in cfg and cfg['yml_analysis']['divide']['flag']:
            self.divide_yaml_files(cfg)
        else:
            raise NotImplementedError("No divide method specified")
        
        return cfg

    def divide_yaml_files(self, cfg) -> None:
        '''
        Iterate through yml files
        '''
        yml_files = cfg['file_management']['input_files']['yml']
        cfg[cfg['basename']] = {'divide': {'groups':[]}}
        for file_name in yml_files:
            cfg_divide = cfg['yml_analysis']['divide']
            if cfg_divide['by'] == 'primary_key':
                logger.debug("Splitting primary keys data START...")
                output_file_name_array = self.divide_yaml_file_by_primary_keys(cfg, file_name)
                cfg[cfg['basename']]['divide']['groups'].append(output_file_name_array)
            else:
                raise Exception("No divide by method specified")
    
    def divide_yaml_file_by_primary_keys(self, cfg, file_name):
        result_folder = cfg['Analysis']['result_folder']
        file_name_stem = Path(file_name).stem
    
        with open(file_name, "r", encoding='utf-8-sig') as file:
            yaml_content = file.read()
            
            cleaned_yaml = self.clean_yaml_file(yaml_content)
            cleaned_yaml = self.extract_data_after_document_start(cleaned_yaml)
            
            data = ruamel_yaml.load(cleaned_yaml)
        
        # Split the YAML into lines for analysis
        lines = cleaned_yaml.splitlines()
        primary_key_info = {}
        current_key = None

        for i, line in enumerate(lines):
            # Check for key definition
            key_match = re.match(r'^([^:]+):', line)
            if key_match:
                current_key = key_match.group(1).strip()
                value_part = line[key_match.end():].strip()
                
                # Check if this is a single-line value
                is_single_line = bool(value_part)  # Starts with content after colon
                
                # Look ahead to see if there are more lines for this value
                if is_single_line and i+1 < len(lines):
                    next_line = lines[i+1]
                    # If next line is indented (more value content) or empty line before next key
                    if next_line and (next_line[0].isspace() or not next_line.strip()):
                        is_single_line = False
                
                primary_key_info[current_key] = is_single_line

        output_file_name_array = []
        for key in data.keys():
            # Skip if the key is marked as single-line in our analysis
            if primary_key_info.get(key, False):
                continue        
                    
            output_file_name = f"{file_name_stem}_{key}.yml"
            output_file_path = os.path.join(result_folder, output_file_name)

            # Post-process the file to convert lists to single-line format
            if cfg['yml_analysis']['shape_output']['flag']:
                with open(output_file_path, "r", encoding='utf-8-sig') as f:
                    content = f.read()
            
                # Apply regex to convert to single-line format
                modified_content = re.sub(
                    r'-\s+-\s+([^\n]+)\n\s+-\s+([^\n]+)',
                    r'- [\1, \2]',
                    content
                )
                
                # Write the modified content back
                with open(output_file_path, "w", encoding='utf-8-sig') as f:
                    f.write(modified_content)
            else:
                with open(output_file_path, "w", encoding='utf-8-sig') as f:
                    ruamel_yaml.dump({key: data[key]}, f)

            output_file_name_array.append({'data':output_file_path})
            
        logger.debug("Splitting primary keys data FINISH...")
        return output_file_name_array
    
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
        return yaml_content

