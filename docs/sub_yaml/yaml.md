## YAML

Yaml is a human readable data serialization format. Used for configuration and data exchange b/w systems.

Usage

```yaml
   key: value
   nested-key:
       - item 1
       - item 2
```

It uses number of spacees for indentation.
Conventionally Two spaces are used for indentation.

Comments:
Represented by "#" character to provide description. these are ignored by yaml

# Comment

key: value # values are listed

Scalars:
Scalars represent simple values Like strings, numbers, etc..
For ex,
String : hello
number : 43
boolean: true
null : null
Scalars don't have any indentation.

Multi-line Scalars :
This is a bit but Similar to scalars but not that much
Multi-line : |
    This is a about
    yaml file format

If Scalar value spans multiple lines  we use | and > Characters ,  otherwise it will give error.
It is also called as key for accessing inside the scalar.

Example. yml :
```Example.yaml :

  name: Samdan
  location: Vijayawada
  Profesion :student
  Hobbies :
     Playing
     Social media
     Programming
  Favourites:
     fruits :grapes
     celeb: Prabhas
  whatisthisabout:
     this is a basic outline of yaml
     File format
```

Note : 
If your yaml file is Syntactically correct (or) not. you can check it in "Yamlint" website.

## References
https://www.educative.io/blog/yaml-tutorial
https://spacelift.io/blog/yaml
https://dev.to/techworld_with_nana/yaml-tutorial-for-beginners-a06


### AI Journal on ruamel.yml font formatting :
Currently, ruamel.yaml doesn't support direct font styling (like italics) in the output YAML files because:

YAML is a plain-text format that doesn't inherently support font styling

ruamel.yaml focuses on preserving content structure, not text rendering

Workarounds you could consider:
1. For display purposes (HTML/PDF):
```python
from ruamel.yaml import YAML
import markdown

yaml = YAML()
data = {"key": "value"}

# Convert to HTML with italic tags
yaml_str = yaml.dump(data)
html_output = f"<pre><i>{yaml_str}</i></pre>"
```
2. Using pseudo-formatting (Unicode italics):
```python
def italicize_text(text):
    # Maps characters to their italic Unicode variants
    italic_map = {
        'a': '𝑎', 'b': '𝑏', 'c': '𝑐', # ... complete mapping needed
        '1': '1', ' ': ' '            # Numbers and spaces stay normal
    }
    return ''.join(italic_map.get(c.lower(), c) for c in text)

# Usage:
styled_yaml = italicize_text(yaml.dump(data))
```
