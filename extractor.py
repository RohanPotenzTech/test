from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from transformers import pipeline


ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
class Extractor:

    @staticmethod
    def extract_links(html, base_url):
        """Extracts all internal links from a webpage."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        base_parsed = urlparse(base_url)
        base_netloc_core = base_parsed.netloc.replace('www.', '')  # Normalize domain

        for a_tag in soup.find_all("a", href=True): 
            href = a_tag["href"].split("#")[0].strip() 

            if not href:
                continue

            if '://' not in href and ':' not in href.split('/')[0].split('?')[0]:
                if href.startswith(base_parsed.netloc + '/'):
                    href = '//' + href
                elif base_parsed.netloc.startswith('www.') and href.startswith(base_netloc_core + '/'):
                    suffix = href[len(base_netloc_core)+1:]
                    href = '//' + base_parsed.netloc + '/' + suffix
                elif not base_parsed.netloc.startswith('www.') and href.startswith('www.' + base_parsed.netloc + '/'):
                    href = '//' + href


            try:
                full_url = urljoin(base_url, href).strip().lower()
                if Extractor.is_internal_link(base_url, full_url):
                    links.add(full_url)
            except ValueError:
                continue  # Skip invalid hrefs

        return links


    @staticmethod
    def is_internal_link(base_url, url):
        """Checks if a URL belongs to the same domain as the base URL."""
        try:
            base_netloc = urlparse(base_url).netloc.replace('www.', '')
            url_netloc = urlparse(url).netloc.replace('www.', '')
            return base_netloc == url_netloc
        except ValueError:
            return False
    
    @staticmethod
    def extract_email(html_content):
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(email_regex, html_content)
    
    @staticmethod
    def extract_names(html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()

        entities = ner_pipeline(text)

        
        organization = []

        for ent in entities:
            if ent["entity_group"] == "ORG":
                organization.append(ent["word"])
        return {
            "organization": list(set(organization))
        }

def main():
    html_content= """
                                    <h1>about us</h1> <a href="xyz.com/a.html">a.html</a>
                                    <a href="b.html">b.html</a>
                                    <a href="c.html">c.html</a>
                                    <a href="www.xyz.com/a.html">d.html</a>
                                    
                                     """

    base = "https://xyz.com/index.html"
    result = Extractor.extract_links(html_content, base)
    print("Internal links with base:", base)
    for link in result:
        print(link)

    print("-" * 40)

    base_www = "https://www.xyz.com/some/path/"
    result_www = Extractor.extract_links(html_content, base_www)
    print("Internal links with base:", base_www)
    for link in result_www:
        print(link)

    
if __name__ == "__main__":
        main()