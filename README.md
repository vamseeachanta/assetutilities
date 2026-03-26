# utilities

Utilities for performing day to day tasks. 

Helps in automation of day to day business tasks for typical business workflows

## Developer Guide

### Overview
This project provides utilities for automating day-to-day business tasks. It includes various scripts and tools to streamline typical business workflows.

### Capabilities
- Web scraping
- Data processing
- Automation scripts
- Integration with other tools
 
### Setups Needed
 
- **Installations** 
    - Python Installation: Ensure Python 3.11 is installed
    - ? install : pip module in python 
    - ? install : pip build submodule ?
    - ? install : conda ? 
    - ? env setup : venv or conda to develop the package ? 
    - ? twine to publish? 
      - is publishing to PyPI being done manually ? 
      - if so, script it. add to dev_tools folder. 
      - we can remove dev_tools from uploaded distribution 
    - how do we formalize these ? into whats needed for 
      - someone just using the binary dist (wheel?) 
      - someone who will build and use locally (sdist?)
      - someone who will just build , use locally and check-in as well 
      - someone who will then package and publish both binary and sdist to PyPI? 
    - upgrade pip if needed ``python.exe -m pip install --upgrade pip``
- **Virtual Environment**: 
```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```
- **dependencies** ``pip install -r dev_tools/requirements.txt``



  
- **run a script**
  - [ ] run a script, python path/to/script.py