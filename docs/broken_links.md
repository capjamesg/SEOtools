# Identify Broken Links

You can identify broken links using the `find_broken_urls()` function.

```python
from seotools import find_broken_urls

urls_to_check = [
    "https://jamesg.blog/",
    "https://jamesg.blog/test/
]

for url in urls_to_check:
    broken_urls = find_broken_urls(url)
    print("Broken URLs identified on " + url + ":")
    print(broken_urls)
```
