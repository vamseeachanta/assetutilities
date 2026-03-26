# Linting

## Summary

pylint

Along with pylint, the other advised linters are:
framework: ruff (or flake8)
typing checks: mypy (or pyright or pylance or pyre)
security checks: bandit
autoformatting: black (or yapf) and isort (for packages)
automated removal of unused imports and variables: autoflake
automatic upgrade of python syntax: pyupgrade
string formating: pydocstringfomatter

### Ruff

Utilize a fast linting solution such as Ruff

<https://github.com/charliermarsh/ruff>
<https://realpython.com/ruff-python/>

### autoflake

Autoflake removes unused imports and unused variables from Python code.

However, it sometimes removes imports that are used in the code. Then using # noqa is the an option to keep these imports. See example code below.

<code>

import matplotlib.pyplot as plt  # noqa

import pandas as pd  # noqa

</code>

### Black

<https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter>

# TODO not working

Run using below command:
<code>
python -m black src
</code>

VS Code settings not working using the code below.

- Need to make "runItOn" commnad to run using python interpreter selected for a project/repo
- (or) point the VS code extention to always run Black using the selected python interpreter

<code>

    "[python]": {
        "editor.formatOnType": true,
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "always"
        },
    },

    "black-formatter.args": [],
    "black-formatter.cwd": [],
    "black-formatter.path": [
        "python",
        "-m",
        "black"
    ],
    "black-formatter.interpreter": [],

    # Could not find python.exe

    "runItOn": {
        "commands": [
            {
                // Python Files Black formatter
                "match": "\\.py$",
                "isShellCommand": true,
                "cmd": "python -m black ${file}",
            },
        ],

    }

</code>

### .toml settings

<code>
[tool.isort]
profile = "black"
import_heading_stdlib = "Standard library imports"
import_heading_thirdparty = "Third party imports"
import_heading_firstparty = "Reader imports"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
line_length = 88

[tool.black]
exclude = '''
/(
.git
| .mypy_cache
| .tox
| venv
| .venv
|_build
| buck-out
| build
| dist
)/
'''
</code>

### VScode settings

<code>

"python.defaultInterpreterPath": "c:\\Users\\vamseea\\AppData\\Local\\miniconda3\\envs\\digitalmodel\\python.exe",
"python.formatting.provider": "black",
"python.terminal.activateEnvironment": true,
"[python]": {
    "editor.formatOnType": true,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "always"
    },
},
"ruff.organizeImports": "false",
"black-formatter.path": {
    "path": [
        "black"
    ]
},
"isort.args": [
    "--profile",
    "black"
],

</code>

### References

<https://github.com/charliermarsh/ruff>

<https://pylint.readthedocs.io/en/stable/>
<https://safjan.com/black-vs-yapf/>

<https://safjan.com/black-change-max-line-length/>

<https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff>

<https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter>

<https://cereblanco.medium.com/setup-black-and-isort-in-vscode-514804590bf9>

<https://python-poetry.org/docs/basic-usage/>
<https://www.markhneedham.com/blog/2023/07/24/vscode-poetry-python-interpreter/>
