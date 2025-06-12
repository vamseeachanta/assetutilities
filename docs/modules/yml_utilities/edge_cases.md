## yaml


### fix ruamel yaml data accessing bug 

when we load yaml content using ruamel , we can't access the data in regular dictionary format.
because it is in ruamel library format. 

```python
data = ruamel_yaml.load(cleaned_yaml)
```
ex : data['some_key'] will give something like below:
```
<CommentedSeq, len() = 1> "
```
so we have to load it in a safe way to access the yml data.

```python
from ruamel.yaml import YAML
safe_yaml = YAML(typ='safe')

data = safe_yaml.load(cleaned_yaml)
```
Now we can access the data as regular dictionary format.


### while loading yml file encountered below error 

❗[ERROR] Exception has occurred: ScannerError ✖
yaml.scanner.ScannerError: while scanning for the next token found character '%' that cannot start any token❗

we can't acutually resolve this bug in a standard way . this is the reason why we solve logically .

**code fix :**

```python
with open(file_name, "r", encoding='utf-8-sig') as file:
    yaml_content = file.read()
    
    # Clean the YAML content
    cleaned_yaml = self.clean_yaml_file(yaml_content)
    
    data = yaml.load(cleaned_yml)

def clean_yaml_file(self,yaml_content):
    """
    Cleans the entire YAML content by removing invalid lines and tokens.
    """
    cleaned_lines = []
    for line in yaml_content.splitlines():
        cleaned_line = self.clean_yaml_line(line)
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)

def clean_yaml_line(self,line):
    """
    Cleans a single line of YAML by removing invalid tokens or characters.
    """
    if '%' in line:
        line = re.sub(r'(\s*[^:]+:\s*)%([^%]+)%', r'\1"\2"', line)  # Wrap %...% in quotes
    return line
```


### While loading yml file , continously getting an error with try except block**

```python
with open(defaultYml, "r") as ymlfile:
      try:
         cfg = yaml.safe_load(ymlfile)
      except yaml.composer.ComposerError as e:
         logger.error(f"YAML parsing error: {e}")
         cfg = self.yml_read_stream(defaultYml)
```

**Solution :**
After introducing encoding format , code goes to except block and then error got resolved.

```python
with open(defaultYml, "r",encoding="utf-8") as ymlfile:
    try:
        cfg = yaml.safe_load(ymlfile)
    except yaml.composer.ComposerError as e:
        logger.error(f"YAML parsing error: {e}")
        cfg = self.yml_read_stream(defaultYml)
```