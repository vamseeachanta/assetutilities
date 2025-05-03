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

**Post-Installation Steps**

### ➕ Add `.venv` to `.gitignore`

```bash
echo ".venv/" >> .gitignore
```

**📁 (Optional) Create Local `.venv` in Project Directory**

```bash
poetry config virtualenvs.in-project true
```

## 🧪 Run Python Scripts in VSCode with Poetry

### 1. (Optional) Enable Local `.venv` in Your Project Root

```bash
poetry config virtualenvs.in-project true
```

### 2. ⚙️ Select the Python Interpreter in VSCode

- Press `Ctrl + Shift + P`
- Type: `Python: Select Interpreter`
- Select the one that looks like: Python 3.11.8 (.venv:Poetry)