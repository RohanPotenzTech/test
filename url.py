import socket
import os
from playwright.sync_api import sync_playwright
from extractor import Extractor
from db_handler import DatabaseHandler
from datetime import datetime, timedelta, UTC
from utils import parse_domain, generate_md5, is_internal_link


class URLHandler:

    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.urls_collection = self.db_handler.urls_collection
        self.domains_collection = self.db_handler.domains_collection

    def fetch_html(self, url):
        """Fetches the HTML content of a URL."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
                page = context.new_page()

                response = page.goto(url, timeout=30000, wait_until='domcontentloaded')
                status_code = response.status if response else None
                html_content = page.content()

                browser.close()
                return html_content, status_code

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None, None

    def get_url_list_last_crawled_48hrs_before(self, num_of_urls=100):
        """Retrieve and lock URLs atomically to prevent duplicate pickups."""
        now = datetime.now(UTC)
        cutoff_time = now - timedelta(hours=48)
        process_id = f"crawler_{os.getpid()}"  # Unique identifier for the process
        hostname = socket.gethostname()
        locked_by = process_id + hostname

        urls_to_find = list(self.urls_collection.find(
            {
                "$or": [
                    {"last_crawled": {"$lt": cutoff_time}},  # Not crawled in 48+ hours
                    {"last_crawled": {"$exists": False}},    # Never crawled
                    {"status": {"$exists": False}},          # No status
                    {"status": {"$in": ["pending", ""]}} 
                ],
            },
            {"_id": 1}  # Fetch only required fields
            ).limit(num_of_urls))

        print(f"Found {len(urls_to_find)} URLs to lock.")

        if not urls_to_find:
            print("No more URLs to process.")
            return []

        url_ids = [url["_id"] for url in urls_to_find]  # Extract IDs to update

        # Lock the URLs by updating their status and adding a process lock
        self.urls_collection.update_many(
            {
                "_id": {"$in": url_ids},
            },
            {
                "$set": {
                    "status": "processing",
                    "locked_at": now,
                    "locked_by": locked_by,
                }
            }
        )

        locked_url_find = list(self.urls_collection.find(
            {
                "$and": [
                    { "_id": {"$in": url_ids} },
                    { "status": "processing" },
                    { "locked_by": locked_by }
                ]
            },
            {"_id": 1, "url": 1, "domain_id": 1, "locked_by": 1}  
        ))

        for url_data in locked_url_find:
            self.process_url(url_data)

    def process_url(self, url):
        """Process a URL by fetching its HTML content and extracting data."""
        html_content, status_code = self.fetch_html(url["url"])
        
        # Check if html_content is None before trying to extract data
        if html_content is None:
            print(f"Error: Could not fetch HTML content for URL {url['url']}")
            self.urls_collection.update_one(
                {"_id": url["_id"], "locked_by": url["locked_by"]},
                {"$set": {
                    "status": "error",
                    "status_code": status_code,
                    "locked_at": None,
                    "locked_by": None,
                    "error_message": "Failed to fetch HTML content"
                }}
            )
            return
            
        # Extract data only if we have HTML content
        emails = Extractor.extract_email(html_content)
        names = Extractor.extract_names(html_content)

        extracted_links = Extractor.extract_links(html_content, url["url"])
        self.store_extracted_links(extracted_links, url)  # Store the extracted links in the database

        # Update the URL status to 'completed' after processing
        self.urls_collection.update_many(
            {"_id": url["_id"], "locked_by": url["locked_by"]},  # Ensure only the same process updates it
            {"$set": {
                "last_crawled": datetime.now(UTC),
                "status": "completed",
                "locked_at": None,
                "locked_by": None,
                "html_content": html_content,
                "status_code": status_code,
                "emails": list(set(emails)),
                "company_names": names["organization"]
            }}
        )
        print(f"Successfully processed and completed URL: {url['url']}")

    def store_extracted_links(self, extracted_links, url):
        """Store extracted links in the database."""
        # Get the normalized domain of the source URL
        source_domain = parse_domain(url["url"])
        
        for link in extracted_links:
            # Normalize the domain of the extracted link
            link_domain = parse_domain(link)
            
            # Determine if this is an internal link
            is_internal = (source_domain == link_domain)
            
            # For internal links, use the source domain_id
            # For external links, we'll need to look up the domain_id from the domain collection
            if is_internal:
                domain_id = url["domain_id"]
            else:
                # Look up the domain_id from the domain collection
                domain_doc = self.domains_collection.find_one({"normalized_domain": link_domain})
                domain_id = domain_doc["_id"] if domain_doc else 0
            
            link = link.strip() 
            link_hash = generate_md5(link)
            
            # Store additional metadata about the link
            link_data = {
                "md5_url": link_hash,
                "url": link,
                "domain_id": domain_id,
                "normalized_domain": link_domain,
                "source_url": url["url"],
                "discovered_at": datetime.now(UTC)
            }
            
            # Use updateOne with upsert to prevent duplicates
            self.urls_collection.update_one(
                {"md5_url": link_hash},   # Find by MD5 hash
                {
                    "$setOnInsert": link_data,
                    "$set": {
                        "last_updated": datetime.now(UTC)
                    }
                },
                upsert=True  # This will insert the link if it's new
            )
            print(f"Link added: {link} (Domain: {link_domain})")