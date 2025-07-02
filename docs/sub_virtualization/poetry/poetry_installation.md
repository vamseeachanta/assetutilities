### Summary

- Poetry is a dependency management tool for Python.
- Poetry is installed in default python directory. It creates its own environment.
- 

Steps using GitBash:
a/ Identify the default python library
<code>
$ which python
b/ Install Poetry using the Python interpreter
```bash
$ curl -sSL https://install.python-poetry.org | /c/Users/Sk\ Samdan/AppData/Local/Programs/Python/Python312/python -
```

## Poetry Setup Guide

### Install poetry on Windows

**🔍 Check Python path**

```bash
$ which python
/c/Users/Sk Samdan/AppData/Local/Programs/Python/Python312/python
```

**📥 Install Poetry**

```bash
$ curl -sSL https://install.python-poetry.org | /c/Users/Sk\ Samdan/AppData/Local/Programs/Python/Python312/python -
```

**🔧 Add Poetry to PATH**

```bash
$ echo 'export PATH="$HOME/AppData/Roaming/Python/Scripts:$PATH"' >> ~/.bashrc
```

Then source the file:

```bash
$ source ~/.bashrc
```

**✅ Verify Installation**

```bash
$ poetry --version
Poetry (version 2.1.2)
```

### Troubleshooting


https://stackoverflow.com/questions/70723486/python-poetry-installation-failed-on-windows-10-no-pyvenv-cfg-file