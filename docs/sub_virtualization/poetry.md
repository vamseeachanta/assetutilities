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

---

### 🚀 Using poetry in existing project

Navigate to your project directory:

```bash
cd your-project/
poetry init
```

- This will prompt you to create a new `pyproject.toml` file.
- You can provide the necessary information or just press `Enter` to accept the defaults.
- If the toml file already exists, you can skip this step.

---

**🛠️ Install the Environment**

```bash
poetry install
```

> ⚠️ It may raise errors like "no matching version found" for a package.  
> 💡 Solution: Check the version availability on [PyPI](https://pypi.org/) and update accordingly.

---

**Post-Installation Steps**

### ➕ Add `.venv` to `.gitignore`

```bash
echo ".venv/" >> .gitignore
```

**📁 (Optional) Create Local `.venv` in Project Directory**

```bash
poetry config virtualenvs.in-project true
```

Re-run:

```bash
poetry install
```

---

## 🧪 Run Python Scripts in VSCode with Poetry

### 1. Enable Local `.venv` in Your Project Root

```bash
poetry config virtualenvs.in-project true
```

### 2. ⚙️ Select the Python Interpreter in VSCode

- Press `Ctrl + Shift + P`
- Type: `Python: Select Interpreter`
- Select the one that looks like: Python 3.11.8 (.venv:Poetry)
- 

#TODO - Utilize self install library with poetry 