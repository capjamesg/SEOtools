[![version](https://badge.fury.io/py/seotools.svg?)](https://badge.fury.io/py/seotools)
[![downloads](https://img.shields.io/pypi/dm/seotools)](https://pypistats.org/packages/seotools)
[![license](https://img.shields.io/pypi/l/seotools?)](https://github.com/capjamesg/seotools/blob/main/LICENSE)
[![python-version](https://img.shields.io/pypi/pyversions/seotools)](https://badge.fury.io/py/mf2py)

# SEOtools 🛠️

A set of utilities for SEOs and web developers with which to complete common tasks.

With SEOtools, you can:

1. Programatically add links to related posts in content.
2. Calculate PageRank on internal links from your sitemap.
3. Identify broken links on a web page.
4. Recommend a post to use as canonical for a given keyword.
5. Find the distance of pages from your home page.

And more!

## Installation 💻

You can install SEOtools using pip:

```bash
pip install seotools
```

## Quickstart 🚀

### Create a link graph

```python
from seotools.app import Analyzer

analyzer = Analyzer("https://jamesg.blog/sitemap.xml")

analyzer.create_link_graph(10, 20)
analyzer.compute_pagerank()
analyzer.embed_headings()
```

### Get pagerank of a URL

```python
print(analyzer.pagerank["https://jamesg.blog"])
```

### Add relevant internal links to a web page

```python
import markdown

article = markdown.markdown(BeautifulSoup(article.text, "html.parser").get_text())

keyword_replace_count = 0

for keyword, url in keyword_map.items():
    if keyword_replace_count >= MAX_KEYWORD_REPLACE:
        break

    article = article.replace(keyword, f"<a href='{url}'>{keyword}</a>", 1)
    keyword_replace_count += 1

print(article)
```

### Recommend related content for a "See Also" section

```python
article = requests.get("https://jamesg.blog/...")

article = markdown.markdown(BeautifulSoup(article.text, "html.parser").get_text())

urls = analyzer.recommend_related_content(article.text)
```

### Check if a page contains a particular JSON-LD object

```python
from seotools import page_contains_jsonld
import requests

content = requests.get("https://jamesg.blog")

print(page_contains_jsonld(content, "FAQPage"))
```

### Get subfolders in a sitemap

```python
analyzer.get_subpaths()
```

### Get distance of URL from home page

```python
analyzer.get_distance_from_home_page("https://jamesg.blog/2023/01/01/")
```

### Retrieve keywords that appear more than N times on a web page

```python
from seotools import get_keywords
import requests
from bs4 import BeautifulSoup

article = requests.get("https://jamesg.blog/...").text
parsed_article = BeautifulSoup(article, "html.parser").get_text()

# get keywords that appear more than 10 times
keywords = get_keywords(parsed_article, 10)
```

## See Also 📚

- [getsitemap](https://github.com/capjamesg/getsitemap): Retrieve URLs in a sitemap. ([Web interface](https://getsitemapurls.com))

## License 📝

This project is licensed under an [MIT license](https://github.com/capjamesg/SEOtools/blob/main/LICENSE).