## Poetry Useful Tips

**Updating dependencies** :

Update , add or remove dependencies in environment.  

```bash
poetry add <package_name>
```

This will install the latest version of package in the environment and add it to the `pyproject.toml` file as well.

```bash
poetry remove <package_name>
```
This will uninstall the package from the environment and removes it from the `pyproject.toml` file as well.

```bash
poetry show 
```
This will show all the dependencies in the environment.

```bash
poetry show --latest
```
This will show the latest version of the dependencies.


**Self installing library in poetry** :

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


references

https://stackoverflow.com/questions/66474844/import-local-package-during-poetry-run