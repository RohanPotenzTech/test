import re
import hashlib

def generate_md5(value):
    """Generates an MD5 hash for a given URL."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()
    
    
def parse_domain(url):
    """Regex to extract the domain from the URL."""
    match = re.search(r'^(?:https?://)?([^/]+)', url)
    if match:
        return match.group(1)  # Extract the domain part
    return None
    