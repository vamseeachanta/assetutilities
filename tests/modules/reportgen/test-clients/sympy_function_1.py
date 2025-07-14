# Standard library imports
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Third party imports
import sympy as sp
import yaml
from loguru import logger
from assetutilities.common.reportgen.reportgen import ReportGenerator 
from assetutilities.common.reportgen.decorator import explain_function

"""
comments to self 

todoz
- [ ] #todo #11_siva #acma_consultation import and use reportgen decorator
- [ ] #todo #11_siva #acma_consultation need better comments , as documentation.

questions/spikes 
 1.  

synthesis 
  1. i went the route of a report generator as a standalone python script independent of the code . 
     - independent module. 
  2. this assignment is still looking for an "inline" util to generate the output. 
     - sympy_function_1 
        - [x] prep : customize yml : easy stuff : 1 header, 1 section - with 1 paragraph that says hello world.
        - [x] load config 
        - [x] default to default flush implementation
        - [x] validate 2 reports are coming out
        - [ ] update decorator to use latest section in dom 
            - [x] ensure basics of reportgen test are working 
            - [x] refactor reportgen to make dom a singleton 
            - [ ] tweak decorator - append paragraphs to current section 
            - [ ] implement thread safety to singleton pattern
            - [ ] nice to have : consider making reportgen a super class, so sympy_function_1 can inherit from it.
            - [ ] reportgen-doris-docx, reportgen-doris-md are broken. target_report_type attribute is being erased somewhere. fixit. 
            - [ ] copy doris_writers to default_writers, make reportgen use default writers if one is not specificied
        - [ ] refactor default flush implementation to default markdown and docx
        - [ ] initializes report generator : easy : use doriswriter 
            - [ ] initializes dorismdwriter (via yml). validate.
            - [ ] check. what will happen if no writer is specified?
            - [ ] then implement a defaultmdwriter (in writers.py). switch to defaultmdwriter (in yml). validate.
                - [ ] does not need logo. can skip header section and so on. make the report/file as simple as needed
        - [ ] defines function 
        - uses reportgenerator to setup dom, report generation capabilities
        - create or set current section as the programming progresses ? 
        - expects decorator to add to current section of the dom ? 
        - then write the dom to a markdown file ? 
     - how does the decorator play into this ? expect the  

brainfarts
  ? this is the dictionary used by sympy_function_1.py ? 
  ? this dictates basic outlines of the report generated ?
  ? and then sympy_function_1.py builds its report by using decorators etc ?
"""

def parse_args():
    logger.info("Parsing command line arguments ...")

    parser = argparse.ArgumentParser(description='SymPy function calculator')
    parser.add_argument('config', help='Path to YAML configuration file')
    return parser.parse_args()

def load_config(config_path: str) -> dict:

    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def write_to_markdown(md_text):
    current_directory = os.path.dirname(os.path.realpath(__file__))
    filename_stem = Path(__file__).stem
    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    filename_md = os.path.join(current_directory, f"{filename_stem}_{timestamp}.out.md")
    with open(filename_md, "w") as out_file:
        out_file.write(md_text)

def print_readable_dict(data: Dict[str, Any]) -> None:
        """Print dictionary in a user-readable format"""
        for key, value in data.items():
            print(f"{key}: {value}")

"""
- [ ] #todo #11_siva #acma_consultation refactor this to take args as input 
"""
def init_report_generator(config: Dict[str, Any]) -> None:    
    global _generator 
    logger.info(f"start using reportgenerator")
    _generator = ReportGenerator()
    _generator.initialize_from_config(config)
    logger.info(f"Initialized reportgenerator using config")
    print_readable_dict(config)

def flush_generator() -> None:    
    _generator.flush_report()

@explain_function(purpose="Small Quadratic Function : ")
def define_function() -> tuple[sp.Expr, sp.Symbol]:
    y = sp.Symbol('y')
    f = y**3 + 4*y + sp.cos(y)
    return f, y

@explain_function(purpose="Integration Function : ")
def integrate_function(f: sp.Expr, y: sp.Symbol) -> tuple[sp.Expr, sp.Symbol]:
    i_f = sp.integrate(f, y)
    logger.info(f"Function Integration is: {i_f}")
    return i_f, y

def main():
    """
    - [ ] #todo #11_siva #acma_consultation validate if log verbosity can be controlled using log level
    """
    # start customization/additions for report generator
    args = parse_args()
    config = load_config(args.config)
    init_report_generator(config)
    # end customization/additions for report generator

    logger.info("Evaluating the integration of the function ...")

    # - [ ] #todo #11_siva #acma_consultation do i refactor this at some time ? think. 
    # - [ ] #todo #11_siva #acma_consultation clean this up later
    # _generator.dom.add_paragraph("\nDefine Function ")
    f, y = define_function()

    # - [ ] #todo #11_siva #acma_consultation clean this up later
    # _generator.dom.add_paragraph("\nIntegrate Function ")
    i_f, y = integrate_function(f, y)

    md_text = "Vamsee original output = \n"
    md_text += 'Function : \n'
    md_text += f'$${sp.latex(f)}$$\n\n'
        
    md_text += 'Integrate function : \n'
    md_text += f'$${sp.latex(i_f)}$$\n\n'
        
    md_text += 'Evaluate at y = 10 : \n'
    y_value = 10
    limit_value = sp.limit(i_f, y, y_value)
    md_text += f'$${sp.latex(limit_value)}$$\n\n'
    
    write_to_markdown(md_text)

    # start customization/additions for report generator
    # not using a decorator, using the generator / dom directly
    _generator.dom.add_paragraph("\nEvaluate at y = 10 : \n Limit Value = ")
    # _generator.dom.add_sympy_expression(limit_value)

    flush_generator()
    # end customization/additions for report generator


main()

