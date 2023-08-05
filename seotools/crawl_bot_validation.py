import socket

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
