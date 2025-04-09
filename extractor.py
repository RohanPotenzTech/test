from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlunparse, urlparse
import re
from transformers import pipeline
from utils import parse_domain

ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
class Extractor:
    
    def normalize_url(url):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return urlunparse((parsed.scheme, domain, parsed.path, '', '', ''))

    @staticmethod
    def extract_links(html, base_url):
        """Extract internal links from HTML based on base_url."""
        soup = BeautifulSoup(html, "html.parser")
        internal_links = set()
        external_links = set()
        
        for a_tag in soup.find_all("a", href=True): 
            href = a_tag["href"].split("#")[0].strip() 

            if not href or href.lower().startswith(("javascript:", "mailto:", "tel:")):
                continue

            try:
                # Handle fake relative domains like "xyz.com/a.html"
                if not href.startswith(("http://", "https://", "/")) and '.' in href.split('/')[0]:
                    href = "http://" + href

                full_url = urljoin(base_url, href).strip().lower()
                normalized = Extractor.normalize_url(full_url)
                if Extractor.is_internal_link(base_url, full_url):
                     internal_links.add(normalized)
                else:
                    external_links.add(normalized)
            except ValueError:
                continue  # Skip invalid hrefs

        return {
            "internal": internal_links,
            "external": external_links
        }

    @staticmethod
    def is_internal_link(base_url, url):
        return parse_domain(base_url) == parse_domain(url)
    
    @staticmethod
    def extract_email(html_content):
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(email_regex, html_content)
    
    @staticmethod
    def extract_names(html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        
        relevant_parts = []

        footer = soup.find("footer")
        if footer:
            relevant_parts.append(footer.get_text(separator=" ", strip=True))

        # Headings (company names often live in h1/h2 tags)
        for tag in soup.find_all(["h1", "h2", "h3"]):
            relevant_parts.append(tag.get_text(separator=" ", strip=True))

        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            relevant_parts.append(meta_author["content"])

        # Combine everything into a single string
        filtered_text = " ".join(relevant_parts)

        entities = ner_pipeline(filtered_text)

        organization = []

        for ent in entities:
            if ent["entity_group"] == "ORG":
                organization.append(ent["word"])
        return {
            "organization": list(set(organization))
        }

def main():
    """Test function for the Extractor class."""
    html_content = """
    <h1>about us</h1> 
    <a href="xyz.com/a.html">a.html</a>
    <a href="/b.html">b.html</a>
    <a href="/c.html">c.html</a>
    <a href="www.xyz.com/d.html">d.html</a>
    <a href="www.pqr.com/e.html">e.html</a>
    <p>Contact us at info@example.com</p>
    <p>Company name: Example Corp</p>
    """

    base = "https://xyz.com/index.html"
    result = Extractor.extract_links(html_content, base)
    print("Internal links with base:", base)
    print("Internal links with base:", base)
    print("\n[Internal Links]")
    for link in result["internal"]:
        print(link)

    print("\n[External Links]")
    for link in result["external"]:
        print(link)
      
if __name__ == "__main__":
    main()