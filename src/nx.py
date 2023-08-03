from collections import Counter

import getsitemap
import indieweb_utils
import networkx as nx
import requests
import sentence_transformers
from bs4 import BeautifulSoup
from pyld import jsonld
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import urlparse
import json

import concurrent.futures


def get_keyword_counts(text):
    return Counter(text.split())


# get all keywords w/ more than N occurrences
def get_keywords(text, limit=10):
    counts = get_keyword_counts(text)

    return [key for key, value in counts.items() if value > limit]


def get_links_in_body(page):
    parsed_page = BeautifulSoup(page.text, "html.parser")
    # waterfall is article, main then body
    # get all links in body
    options = ["article", "main", "body"]

    while options:
        option = options.pop(0)

        body = parsed_page.find(option)

        if body:
            break

    links = body.find_all("a", href=True)

    return links


def page_contains_jsonld(page, jsonld_type):
    # check if page contains json-ld
    # if so, return it
    # else return None
    parsed_page = BeautifulSoup(page.text, "html.parser")
    scripts = parsed_page.find_all("script", attrs={"type": "application/ld+json"})

    for script in scripts:
        jsonld_data = jsonld.loads(script.text)

        if jsonld_data["@type"] == jsonld_type:
            return jsonld_data

    return None


def get_page_urls(url):
    # use browser UA
    page = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
        },
    )
    parsed_page = BeautifulSoup(page.text, "html.parser")
    # get all h1s, h2s
    # headings = parsed_page.find_all(["h1", "h2"])
    # headings = [heading.text for heading in headings]
    # make headings all article text
    headings = [parsed_page.get_text()]

    return parsed_page.find_all("a", href=True), url, headings


class Analyzer:
    def __init__(self, url):
        self.sitemap_url = url
        self.domain = urlparse(url).netloc
        link_graph = nx.DiGraph()

    def create_link_graph(self):
        # exploratory internal linking
        # def recommend_canonical : recommend a best canonical for a given keyword
        # search PRs for given keyword
        # get all subfolders

        sitemap_urls = getsitemap.get_individual_sitemap(SITEMAP_URL)

        internal_link_count = {}
        heading_information = {}

        # get pagerank
        G = nx.DiGraph()

        for url in sitemap_urls[SITEMAP_URL]:
            G.add_node(url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
            urls = sitemap_urls[SITEMAP_URL]  # [:3]

            processes = [executor.submit(get_page_urls, url) for url in urls]

            for process in concurrent.futures.as_completed(processes):
                try:
                    result = process.result()

                    if not result:
                        continue

                    links, url, headings = result
                    heading_information[url] = headings

                    for link in links:
                        # track all internal links
                        # canonicalize link
                        link["href"] = indieweb_utils.canonicalize_url(
                            link["href"], self.domain, "https"
                        )

                        # must start with https
                        if not link["href"].startswith("https"):
                            continue

                        link["href"] = link["href"].split("#")[0]
                        link["href"] = link["href"].split("?")[0]
                        link["href"] = link["href"].strip("/").strip()

                        if (
                            self.domain in link["href"]
                            and link["href"] != url
                            and link["href"]
                            not in internal_link_count.get(link["href"], [])
                        ):
                            internal_link_count[link["href"]] = internal_link_count.get(
                                link["href"], []
                            ) + [url]
                            G.add_edge(url, link["href"])

                except Exception as e:
                    raise e

        # dedupe all internal links
        for key, value in internal_link_count.items():
            internal_link_count[key] = list(set(value))

        self.link_graph = G
        self.internal_link_count = internal_link_count

        self.max_page_count = max(
            [len(value) for value in internal_link_count.values()]
        )

    def remove_most_common_links(self):
        # used for removing navigation and footer links
        # remove all links that are on 90% of pages
        result = {}

        for key, value in self.internal_link_count.items():
            if len(value) < 0.9 * self.max_page_count:
                result[key] = value

        return result

    def compute_pagerank(self):
        pagerank = nx.pagerank(self.link_graph)

        # order by pagerank in desc
        sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)

        return sorted_pagerank

    def save(self):
        with open("pagerank.json", "w") as f:
            json.dump(self.sorted_pagerank, f, indent=2)

        # save counts
        with open("internal_link_count.json", "w") as f:
            json.dump(self.internal_link_count, f, indent=2)

        # save headings
        with open("heading_information.json", "w") as f:
            json.dump(self.heading_information, f, indent=2)

    def embed_headings(self):
        # embed headings
        model = sentence_transformers.SentenceTransformer(
            "paraphrase-distilroberta-base-v1"
        )

        heading_embeddings = {}

        for url, headings in self.heading_information.items():
            concatenated_headings = " ".join(headings)
            heading_embeddings[url] = model.encode(concatenated_headings)

        self.heading_embeddings = heading_embeddings

    def find_most_similar_post_to_query(self, query):
        query_embedding = self.model.encode(query)

        similarities = {}

        for url, embedding in self.heading_embeddings.items():
            similarities[url] = cosine_similarity([query_embedding], [embedding])[0][0]

        serialized_similarities = {k: v.tolist() for k, v in similarities.items()}

        # zip similarities with PR
        sorted_similarities_with_pr = {}

        for url, similarity in serialized_similarities.items():
            sorted_similarities_with_pr[url] = {
                "similarity": similarity,
                "pagerank": self.pagerank[url],
            }

        # return top 10 results
        last_heading_similarity = sorted(
            sorted_similarities_with_pr.items(),
            key=lambda x: x[1]["similarity"],
            reverse=True,
        )[:10]

        self.last_heading_similarity = last_heading_similarity

    def is_canonical_best_linked(self, canonical):
        if canonical not in self.last_heading_similarity:
            return False

        return self.last_heading_similarity.index(canonical) == 0

    def _load_model(self):
        self.model = sentence_transformers.SentenceTransformer(
            "paraphrase-distilroberta-base-v1"
        )

    def recommend_canonical(self, query):
        if not self.model:
            self.model = self._load_model()

        query_embedding = self.model.encode(query)

        similarities = {}

        for url, embedding in self.heading_embeddings.items():
            similarities[url] = cosine_similarity([query_embedding], [embedding])[0][0]

        sorted_similarities = sorted(
            similarities.items(), key=lambda x: x[1], reverse=True
        )[:1]

        canonical = sorted_similarities[0][0]

        return canonical
