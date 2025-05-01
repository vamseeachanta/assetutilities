### create poetry environment

> pyproject.toml 

if your project doesn't have pyproject.toml , navigate to your project and run 'poetry init' 
else modify existing pyproject.toml file to be compatible with poetry

> create virtual environment via requirements.txt 
    
```bash
poetry run pip install -r requirements.txt

ex : poetry run pip install -r ./dev_tools/requirements.txt
```
- environment will be created in the current directory with the name .venv
- if you wanna check packages in env 'poetry show' doesn't work (bcoz we used pip) , so prefer below command 

```bash
poetry run pip list
```


> Self installing library into environment

Include your local repo as below in your `pyproject.toml` file:

```
[tool.poetry.dependencies]
assetutilities = { path = "../assetutilities", develop = true }
```

run `poetry install` to install the library into the environment.

> If there's an error with python version, you need to specify the compatible python version in the `pyproject.toml` file:

```
[tool.poetry.dependencies]
assetutilities = { path = "../assetutilities", develop = true }
python = "^3.8"
```

again , run `poetry install` to install the environment.

> Installing via Poetry has the advantage of allowing us to utilize all of its features.

- poetry show - shows the packages installed in the environment
- poetry add <package_name> - to add a new package to the environment
- poetry remove <package_name> - to remove a package from the environment
- poetry update - to update the packages in the environment

if poetry like commands doesn't work , we have to use pip commands like below:

- poetry run pip list - to view the packages in the environment
- poetry pip show <package_name> - to view the details of a specific package in the environment

> Managing the dependencies in the environment

**Add a new package**
- add package manually in requirements.txt file and run the below command

```bash
poetry run pip install -r requirements.txt
```

**Remove a package**
```
poetry pip uninstall <package_name>
```
poetry run pip install -r requirements.txt - updates the environment
