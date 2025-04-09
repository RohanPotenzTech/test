import re
import hashlib
from urllib.parse import urlparse, urljoin

def generate_md5(value):
    """Generates an MD5 hash for a given URL."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()
    
    
def parse_domain(url):
    """Regex to extract the domain from the URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.lower()
    except Exception:
        match = re.search(r'^(?:https?://)?([^/]+)', url)
    if match:
        return match.group(1)  # Extract the domain part
    return None


    