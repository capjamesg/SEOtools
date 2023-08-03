import concurrent.futures
import socket

import requests

GOOGLE_BOT_HOSTS = ["googlebot.com", "google.com", "googleusercontent.com"]


def is_google_owned_resource(ip: str) -> bool:
    """
    Check if the IP address is owned by Google.

    Args:
        ip (str): The IP address to check.

    Returns:
        bool: True if the IP address is owned by Google, False otherwise.
    """
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname in GOOGLE_BOT_HOSTS
    except:
        return False


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
