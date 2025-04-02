from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class Extractor:
    @staticmethod
    def extract_links(html, base_url):
        """Extracts all internal links from a webpage."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].split("#")[0].strip() 
            full_url = urljoin(base_url, href).strip().lower()

            if Extractor.is_internal_link(base_url, full_url):
                links.add(full_url)

        return links

    @staticmethod
    def is_internal_link(base_url, url):
        """Checks if a URL belongs to the same domain as the base URL."""
        return urlparse(url).netloc == urlparse(base_url).netloc
