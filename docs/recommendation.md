# Content Recommendations

You can use SEOtools for content recommendation.

There are two methods of recommending content:

1. Automatically adding relevant links to a web page.
2. Identifying content for a "See Also" (aka "Related Posts") section.

This guide uses the Analyzer() class. Read the full[Analyzer() documentation](reference/analyzer.md) for more information.

## Add relevant links to a web page

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

