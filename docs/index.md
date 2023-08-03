# SEOtools 🛠️

A set of utilities for SEOs and web developers with which to complete common tasks.

With SEOtools, you can:

1. Programatically add links to related posts in content.
2. Calculate PageRank on internal links from your sitemap.
3. Identify broken links on a web page.
4. Recommend a post to use as canonical for a given keyword.
5. Find the distance of pages from your home page.

And more!

## Installation

You can install SEOtools using pip:

```bash
pip install seotools
```

## Quickstart

### Create a link graph

```python
from seotools.app import Analyzer

analyzer = Analyzer("https://jamesg.blog/sitemap.xml")

analyzer.create_link_graph(10, 20)
analyzer.compute_pagerank()
analyzer.embed_headings()
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

## See Also

- [getsitemap](https://github.com/capjamesg/getsitemap): Retrieve URLs in a sitemap. ([Web interface](https://getsitemapurls.com))

## License

This project is licensed under an [MIT license](https://github.com/capjamesg/SEOtools/blob/main/LICENSE).