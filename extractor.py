from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from utils import is_internal_link, parse_domain

class Extractor:

    @staticmethod
    def normalize_domain(url):
        """Normalizes a domain to its canonical form.
        
        Args:
            url (str): The URL or domain to normalize
            
        Returns:
            str: The normalized domain (e.g., 'xyz.com' from 'www.xyz.com' or 'https://www.xyz.com/')
        """
        return parse_domain(url)

    @staticmethod
    def extract_links(html, base_url):
        """Extracts all internal links from a webpage."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        base_domain = parse_domain(base_url)

        for a_tag in soup.find_all("a", href=True): 
            href = a_tag["href"].split("#")[0].strip() 

            if not href:
                continue

            try:
                full_url = urljoin(base_url, href).strip().lower()
                if is_internal_link(base_url, full_url):
                    links.add(full_url)
            except ValueError:
                continue  # Skip invalid hrefs

        return links

    @staticmethod
    def is_internal_link(base_url, url):
        """Checks if a URL belongs to the same domain as the base URL."""
        return is_internal_link(base_url, url)
    
    @staticmethod
    def extract_email(html_content):
        """Extracts email addresses from HTML content."""
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(email_regex, html_content)
    
    @staticmethod
    def extract_names(html_content):
        """Extracts organization names from HTML content."""
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Look for common organization indicators
        org_patterns = [
            r'(?i)company\s+name:\s*([A-Za-z0-9\s&.,]+)',
            r'(?i)organization:\s*([A-Za-z0-9\s&.,]+)',
            r'(?i)about\s+([A-Za-z0-9\s&.,]+)',
            r'(?i)welcome\s+to\s+([A-Za-z0-9\s&.,]+)',
            r'(?i)©\s*(\d{4})\s*([A-Za-z0-9\s&.,]+)',
            r'(?i)all\s+rights\s+reserved\s+([A-Za-z0-9\s&.,]+)',
            r'(?i)<title>([^<]+)</title>',
            r'(?i)<h1[^>]*>([^<]+)</h1>',
            r'(?i)<h2[^>]*>([^<]+)</h2>',
            r'(?i)<meta\s+name="description"\s+content="([^"]+)"',
        ]
        
        organizations = set()
        for pattern in org_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if isinstance(match, tuple):
                    # If the pattern has groups, take the organization name group
                    org_name = match[-1].strip()
                else:
                    org_name = match.strip()
                if org_name:
                    organizations.add(org_name)
        
        return {
            "organization": list(organizations)
        }

def main():
    """Test function for the Extractor class."""
    html_content = """
    <h1>about us</h1> 
    <a href="xyz.com/a.html">a.html</a>
    <a href="b.html">b.html</a>
    <a href="c.html">c.html</a>
    <a href="www.xyz.com/a.html">d.html</a>
    <p>Contact us at info@example.com</p>
    <p>Company name: Example Corp</p>
    """

    base = "https://xyz.com/index.html"
    result = Extractor.extract_links(html_content, base)
    print("Internal links with base:", base)
    for link in result:
        print(link)
        # Demonstrate domain normalization
        normalized_domain = Extractor.normalize_domain(link)
        print(f"  Normalized domain: {normalized_domain}")

    print("-" * 40)

    base_www = "https://www.xyz.com"
    result_www = Extractor.extract_links(html_content, base_www)
    print("Internal links with base:", base_www)
    for link in result_www:
        print(link)
        # Demonstrate domain normalization
        normalized_domain = Extractor.normalize_domain(link)
        print(f"  Normalized domain: {normalized_domain}")
    
    print("-" * 40)
    
    # Test email extraction
    emails = Extractor.extract_email(html_content)
    print("Extracted emails:", emails)
    
    # Test organization name extraction
    names = Extractor.extract_names(html_content)
    print("Extracted organization names:", names["organization"])
    
if __name__ == "__main__":
    main()