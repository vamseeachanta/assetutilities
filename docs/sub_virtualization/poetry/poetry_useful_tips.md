## Poetry Useful Tips

### env

**Activate env**
find poetry path:
```
poetry env info --path
C:\Users\Sk Samdan\Desktop\github\assethold\.venv
```

activate the environment:
```
C:\Users\Sk Samdan\Desktop\github\assethold\.venv\Scripts\activate
```

**env info**
```
poetry env info
```

**delete env**
```
poetry env remove /full/path/to/python
poetry env remove python3.7
```

You can delete more than one environment at a time.
```
poetry env remove python3.7 python3.8
```
Use the --all option to delete all virtual environments at once.
```
poetry env remove --all
```


**Basic commands**

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

https://python-poetry.org/docs/cli/
https://stackoverflow.com/questions/66474844/import-local-package-during-poetry-run