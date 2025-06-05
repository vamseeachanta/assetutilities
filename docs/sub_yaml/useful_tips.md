# yaml

While loading yml file , continously getting an error with try except block

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