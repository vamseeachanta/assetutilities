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


**Self installing library in poetry** 

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


references:

https://stackoverflow.com/questions/66474844/import-local-package-during-poetry-run