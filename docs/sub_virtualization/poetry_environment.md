### create poetry environment

**pyproject.toml** 

poetry uses pyproject.toml file as a main tool for virtual environment.

if your project doesn't have pyproject.toml , navigate to your project and run 'poetry init' 
else modify existing pyproject.toml file to be compatible with poetry

**create virtual environment via requirements.txt** 
    
```bash
poetry run pip install -r requirements.txt

ex : poetry run pip install -r ./dev_tools/requirements.txt
```
- environment will be created in the current directory with the name .venv
- if you wanna check packages in env 'poetry show' doesn't work (bcoz we used pip) , so prefer below command 

```bash
poetry run pip list
```

**Install local repository into environment**

Include your local repo , path as below in your `pyproject.toml` file:

```
[tool.poetry.dependencies]
assetutilities = { path = "../assetutilities", develop = true }
```

run `poetry install` to install it into the environment.

> If there's an error with python version, you need to specify the compatible python version fro the error in the `pyproject.toml` file:

```
[tool.poetry.dependencies]
assetutilities = { path = "../assetutilities", develop = true }
python = "^3.8"
```

again , run `poetry install` to install the environment.

> Installing via Poetry has the advantage of allowing us to utilize all of its features like below

- poetry show - shows the packages installed in the environment
- poetry add <package_name> - to add a new package to the environment
- poetry remove <package_name> - to remove a package from the environment
- poetry update - to update the packages in the environment

## 🧪 Run Python Scripts in VSCode with Poetry

### (Optional) Enable Local `.venv` in Your Project Root

```bash
poetry config virtualenvs.in-project true
```

### ⚙️ Select the Python Interpreter in VSCode

- Press `Ctrl + Shift + P`
- Type: `Python: Select Interpreter`
- Select the one that looks like: Python 3.11.8 (.venv:Poetry)