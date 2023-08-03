# Validate Googlebot IPs

Use the `is_google_owned_resource()` function to verify if a given IP address is owned by Google.

:::seotools.crawl_bot_validation.is_google_owned_resource

```python
from seotools import is_google_owned_resource

if is_google_owned_resource("0.0.0.0"):
    print("This IP address is owned by Google.")
else:
    print("This IP address is not owned by Google.")
```