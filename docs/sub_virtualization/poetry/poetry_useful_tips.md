## Poetry Useful Tips

add new package to the environment:

```bash
poetry add <package_name>
```

remove package from the environment:

```bash
poetry remove <package_name>
```

show all the dependencies in the environment:

```bash
poetry show 
```

show latest version of the dependencies:

```bash
poetry show --latest
```

**Install local repository into environment** 

In pyproject.toml file, add the following code to install a library from a local path:

```toml
[tool.poetry.dependencies]
my_library = { path = "../my_library", develop = true }

Ex:
[tool.poetry.dependencies]
assetutilities = { path = "../assetutilities", develop = true }

```
and then update the the environment using command :

```bash
poetry update
```

Verify the installation using:

```bash
poetry show
```
This will list out the library in the environment.


**Poetry environment via requirements.txt**

poetry created via requirements.txt file will not be compatible with poetry commands.
So, we need to use pip commands to manage the environment.

- poetry run pip list - to view the packages in the environment
- poetry pip show <package_name> - to view the details of a specific package in the environment

### Managing the dependencies 

**Add a new package**

```bash
add package manually in requirements.txt file and run
poetry run pip install -r requirements.txt
```

**Remove a package**
```bash
poetry pip uninstall <package_name>
and update environment :
poetry run pip install -r requirements.txt 
```

references:

https://stackoverflow.com/questions/66474844/import-local-package-during-poetry-run