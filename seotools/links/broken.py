import concurrent.futures

import requests


def find_broken_urls(urls: list, timeout: int = 5) -> list:
    """
    Find broken URLs.

    Args:
        urls (list): A list of URLs to check.
        timeout (int, optional): The timeout in seconds. Defaults to 5.

    Returns:
        list: A list of broken URLs.
    """
    broken_urls = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(requests.get, url, timeout=timeout): url for url in urls
        }
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]

            try:
                response = future.result()
                if response.status_code != 200:
                    broken_urls.append(url)

            except Exception as exc:
                broken_urls.append(url)
                print(f"{url} generated an exception: {exc}")

    return broken_urls


print(find_broken_urls(["https://jamesg.blog"]))
