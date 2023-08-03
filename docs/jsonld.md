# Identify JSON-LD

You can use the `page_contains_jsonld()` function to identify if a page contains a specific JSON-LD type (i.e. `FAQPage` or `Article`). This is useful for validating the presence of structured data on pages across a website.

`page_contains_jsonld()` does not validate the JSON-LD schema. It only checks if a page contains a JSON-LD object of a particular type.

```python
from seotools import page_contains_jsonld
import requests

page_content = requests.get("https://jamesg.blog").text

print(page_contains_jsonld(page_content, "FAQPage"))
```