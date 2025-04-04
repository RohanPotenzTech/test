from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline


ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
class Extractor:
    def __init__(self):
        model_name = "dslim/bert-base-NER"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.ner_pipeline = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")  

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
    
    @staticmethod
    def extract_email(html_content):
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(email_regex, html_content)
    
    @staticmethod
    def extract_names(html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()

        ner_results = ner_pipeline(text)

        persons = set()
        organization = set()

        for ent in ner_results:
            if ent["entity_group"] == "PER":
                persons.add(ent["word"])
            elif ent["entity_group"] == "ORG":
                organization.add(ent["word"])
        return {
            "peron_names": list(persons),
            "company_names": list(organization)
        }