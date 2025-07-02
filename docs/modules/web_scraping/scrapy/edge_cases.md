
Encountered below error while running scrapy spider:

```
RuntimeError: The installed reactor (twisted.internet.selectreactor.SelectReactor) does not match the requested one (twisted.internet.asyncioreactor.AsyncioSelectorReactor)
```

Solution:
To resolve this error, we need to ensure proper package versions and reactor compatibility. 
- scrapy
- twisted
- crochet