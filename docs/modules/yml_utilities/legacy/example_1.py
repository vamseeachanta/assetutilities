import sys
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap as CM
from ruamel.yaml.comments import Format, Comment


yaml_str = """\
# example YAML document
abc: All Strings are Equal  # but some Strings are more Equal then others
klm: Flying Blue
xYz: the End                # for now
"""

def fkey(s):
    return s.upper()

def fval(s):
    return s.lower()

def transform(data, fk, fv):
    d = CM()
    if hasattr(data, Format.attrib):
        setattr(d, Format.attrib, getattr(data, Format.attrib))
    ca = None
    if hasattr(data, Comment.attrib):
        setattr(d, Comment.attrib, getattr(data, Comment.attrib))
        ca = getattr(d, Comment.attrib)
    # as the key mapping could map new keys on old keys, first gather everything
    key_com = {}
    for k in data:
        new_k = fk(k)
        d[new_k] = fv(data[k])
        if ca is not None and k in ca.items:
            key_com[new_k] = ca.items.pop(k)
    if ca is not None:
        assert len(ca.items) == 0
        ca._items = key_com  # the attribute, not the read-only property
    return d

yaml = ruamel.yaml.YAML()
data = yaml.load(yaml_str)

# the following will print any new CommentedMap with curly braces, this just here to check
# if the style attribute copying is working correctly, remove from real code
yaml.default_flow_style = True

data = transform(data, fkey, fval)
yaml.dump(data, sys.stdout)