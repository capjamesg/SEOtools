import concurrent.futures
import json
import re
from collections import Counter
from urllib.parse import urlparse

import getsitemap
import indieweb_utils
import networkx as nx
import requests
import sentence_transformers
from bs4 import BeautifulSoup
from pyld import jsonld
from sklearn.metrics.pairwise import cosine_similarity


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

    return False


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
        self.model = None
        self.reverse_link_graph = None

    def get_subpaths(self) -> list:
        """
        Get all subpaths on a site.

        :return: A list of subpaths.
        :rtype: list
        """
        subpaths = {}

        for url in self.link_graph.nodes:
            url = url.replace(url.strip("/").split("/")[-1], "").strip("/")
            subpaths[url] = subpaths.get(url, []) + [url]

        return subpaths

    def create_link_graph(self, max_workers=20, url_limit=None) -> None:
        """
        Create a link graph of all internal links on a site.

        :param max_workers: The maximum number of threads to use.
        :type max_workers: int
        :param url_limit: The maximum number of URLs to process.
        :type url_limit: int

        :return: None
        :rtype: None
        """

        sitemap_urls = getsitemap.get_individual_sitemap(self.sitemap_url)

        print(f"Found {len(sitemap_urls)} sitemaps")

        # strip / from end of all URLs
        for key, value in sitemap_urls.items():
            sitemap_urls[key] = [url.strip("/") for url in value]

        reverse_link_graph = nx.DiGraph()

        self.reverse_link_graph = reverse_link_graph

        internal_link_count = {}
        heading_information = {}

        # get pagerank
        G = nx.DiGraph()

        for url in sitemap_urls[self.sitemap_url]:
            G.add_node(url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            if url_limit:
                urls = sitemap_urls[self.sitemap_url][:url_limit]  # [:3]
            else:
                urls = sitemap_urls[self.sitemap_url]

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
                        link["href"] = link["href"].strip("/")

                        if (
                            self.domain in link["href"]
                            and link["href"] != url
                            and link["href"]
                            not in internal_link_count.get(link["href"], [])
                        ):
                            internal_link_count[link["href"]] = internal_link_count.get(
                                link["href"], []
                            ) + [url]
                            G.add_node(link["href"])
                            G.add_edge(url, link["href"])

                            # reverse_link_graph.add_node(url)
                            # reverse_link_graph.add_node(link["href"])

                            # reverse_link_graph.add_edge(link["href"], url)

                except Exception as e:
                    raise e

        self.heading_information = heading_information

        # dedupe all internal links
        for key, value in internal_link_count.items():
            internal_link_count[key] = list(set(value))

        self.link_graph = G
        self.internal_link_count = internal_link_count

        self.max_page_count = max(
            [len(value) for value in internal_link_count.values()]
        )

        # calculate distance between homepage and https://jamesg.blog/category/coffee

        # distance = nx.shortest_path_length(
        #     self.link_graph, "https://" + self.domain, "https://" + self.domain + "/category/coffee"
        # )
        # https://jamesg.blog/category/ -> https://jamesg.blog/category/coffee
        # print(f"Distance: {distance}")

    def remove_most_common_links(self):
        # used for removing navigation and footer links
        # remove all links that are on 90% of pages
        result = {}

        for key, value in self.internal_link_count.items():
            if len(value) < 0.9 * self.max_page_count:
                result[key] = value

        return result

    def compute_pagerank(self) -> dict:
        """
        Compute the pagerank of each page in the link graph.

        :return: A dictionary of URLs and their pagerank.
        :rtype: dict
        """
        pagerank = nx.pagerank(self.link_graph)

        # order by pagerank in desc
        sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        self.pagerank = pagerank

        return sorted_pagerank

    def save(self) -> None:
        """
        Save the results of an analysis to disk.
        """

        if self.pagerank:
            with open("pagerank.json", "w") as f:
                json.dump(self.pagerank, f, indent=2)

        if self.link_graph:
            with open("link_graph.json", "w") as f:
                # save as json
                link_graph_as_json = nx.node_link_data(self.link_graph)

                json.dump(link_graph_as_json, f, indent=2)

        # save counts
        if self.internal_link_count:
            with open("internal_link_count.json", "w") as f:
                json.dump(self.internal_link_count, f, indent=2)

        # save headings
        if self.heading_information:
            with open("heading_information.json", "w") as f:
                json.dump(self.heading_information, f, indent=2)

    def _get_distance_from_homepage(self, url: str) -> int:
        """
        Get the distance from the homepage of a URL.

        :param url: The URL to check.
        :type url: str

        :return: The distance from the homepage.
        :rtype: int
        """
        if not self.link_graph or url not in self.link_graph.nodes:
            return -1

        # crawl from homepage to url

        # visualize reverse link graph

        # from matplotlib import pyplot as plt

        # nx.draw(self.reverse_link_graph, with_labels=True)
        # plt.show()

        # get all paths from homepage to url
        if "https://" + self.domain not in self.link_graph.nodes:
            return -1

        try:
            return nx.shortest_path_length(
                self.link_graph, "https://" + self.domain, url
            )
        except nx.NetworkXNoPath:
            print(f"No path from homepage to {url}")
            return -1

    def get_distances_from_homepage(self) -> dict:
        """
        Get the distance from the homepage of all URLs.

        :return: A dictionary of URLs and their distance from the homepage.
        :rtype: dict
        """
        distances = {}

        for url in self.link_graph.nodes:
            distance = self._get_distance_from_homepage(url)

            if distance == -1:
                continue

            distances[url] = distance

        return distances

    def embed_headings(self) -> None:
        """
        Create embeddings for all headings on a site.

        :return: None
        :rtype: None
        """
        model = sentence_transformers.SentenceTransformer(
            "paraphrase-distilroberta-base-v1"
        )

        heading_embeddings = {}

        for url, headings in self.heading_information.items():
            concatenated_headings = " ".join(headings)
            heading_embeddings[url] = model.encode(concatenated_headings)

        self.heading_embeddings = heading_embeddings

    def find_most_similar_post_to_query(self, query: str) -> None:
        """
        Find the most similar post to a query.

        :param query: The query to use.
        :type query: str

        :return: None
        :rtype: None
        """
        if not self.model:
            self.model = self._load_model()

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

    def is_canonical_best_linked(self, canonical: str) -> bool:
        """
        Check if the canonical URL is the best linked to page.

        :param canonical: The canonical URL.
        :type canonical: str

        :return: Whether or not the canonical URL is the best linked to page.
        :rtype: bool
        """

        if canonical not in self.last_heading_similarity:
            return False

        return self.last_heading_similarity.index(canonical) == 0

    def _load_model(self) -> sentence_transformers.SentenceTransformer:
        return sentence_transformers.SentenceTransformer(
            "paraphrase-distilroberta-base-v1"
        )

    def _recommend(self, query: str) -> str:
        """
        Recommend a canonical URL for use with internal link optimization.

        :param query: The query to use.
        :type query: str

        :return: The canonical URL.
        :rtype: str
        """
        if not self.model:
            self.model = self._load_model()

        query_embedding = self.model.encode(query)

        similarities = {}

        for url, embedding in self.heading_embeddings.items():
            similarities[url] = cosine_similarity([query_embedding], [embedding])[0][0]

        sorted_similarities = sorted(
            similarities.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return sorted_similarities

    def recommend_canonical(self, query):
        return self._recommend(query)[0][0]

    def recommend_related_content(self, query, allowed_directories=None):
        allowed_directories = [i.lstrip("/") for i in allowed_directories]

        results = [url for url, _ in self._recommend(query)]

        if allowed_directories:
            results = [
                url
                for url in results
                if re.match(
                    f"https://{self.domain}/({'|'.join(allowed_directories)})",
                    url,
                )
            ]

        return results
