## Poetry in CMD

### How to make Poetry executable in Command Prompt

steps:
1. Find where poetry has installed in your system
```bash
where poetry
C:\Users\Sk Samdan\AppData\Roaming\Python\Scripts\poetry.exe

```
2. Add it to environment variables

Steps:

1️⃣ Press Win + S → Search Environment Variables
2️⃣ Click Edit the system environment variables → Environment Variables
3️⃣ Under User variables → select Path → click Edit
4️⃣ Click New → add:

C:\Users\Sk Samdan\AppData\Roaming\Python\Scripts
5️⃣ Click OK → OK → OK

3️⃣ Restart Command Prompt
Open a fresh Command Prompt:
```bash
poetry --version
```

### Running python scripts with Poetry

steps:
1. activate environment
refer ![alt text](poetry_useful_tips.md)

2. run the script
```
python script.py
```

