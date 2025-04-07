import re
import hashlib
from urllib.parse import urlparse, urljoin

def generate_md5(value):
    """Generates an MD5 hash for a given URL."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()
    
def parse_domain(url):
    """Extracts the domain from a URL.
    
    Args:
        url (str): The URL to parse
        
    Returns:
        str: The domain part of the URL (e.g., 'example.com')
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain.lower()
    except Exception:
        # Fallback to regex if urlparse fails
        match = re.search(r'^(?:https?://)?(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1).lower()
        return None

def is_valid_url(url):
    """Checks if a URL is valid.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url):
    """Normalizes a URL to a standard format.
    
    Args:
        url (str): The URL to normalize
        
    Returns:
        str: The normalized URL
    """
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # Parse the URL
    parsed = urlparse(url)
    
    # Reconstruct with normalized components
    normalized = f"{parsed.scheme}://{parsed.netloc.lower()}"
    
    # Add path if it exists
    if parsed.path:
        normalized += parsed.path
        
    # Add query if it exists
    if parsed.query:
        normalized += f"?{parsed.query}"
        
    # Add fragment if it exists
    if parsed.fragment:
        normalized += f"#{parsed.fragment}"
        
    return normalized

def is_same_domain(url1, url2):
    """Checks if two URLs belong to the same domain.
    
    Args:
        url1 (str): First URL
        url2 (str): Second URL
        
    Returns:
        bool: True if both URLs belong to the same domain
    """
    domain1 = parse_domain(url1)
    domain2 = parse_domain(url2)
    
    if not domain1 or not domain2:
        return False
        
    return domain1 == domain2

def is_internal_link(base_url, url):
    """Checks if a URL belongs to the same domain as the base URL.
    
    Args:
        base_url (str): The base URL
        url (str): The URL to check
        
    Returns:
        bool: True if the URL belongs to the same domain as the base URL
    """
    return is_same_domain(base_url, url)

def extract_links_from_html(html, base_url):
    """Extracts all links from HTML content.
    
    Args:
        html (str): The HTML content
        base_url (str): The base URL
        
    Returns:
        set: A set of extracted links
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].split("#")[0].strip()
        
        if not href:
            continue
            
        try:
            full_url = urljoin(base_url, href).strip().lower()
            links.add(full_url)
        except ValueError:
            continue  # Skip invalid hrefs
            
    return links
    