import socket
import os
from playwright.sync_api import sync_playwright
from extractor import Extractor
from db_handler import DatabaseHandler
from datetime import datetime, timedelta, UTC
from utils import parse_domain, generate_md5


class URLHandler:

    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.urls_collection = self.db_handler.db["urls"]
        self.domains_collection = self.db_handler.db["domains"]

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
            print(f" Error fetching {url}: {e}")
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
                    {"last_crawled": {"$exists": False}},    # Never crawled
                    {"last_crawled": {"$lt": cutoff_time}},  #  Not crawled in 48+ hours
                    {"status": {"$exists": False}},          # No status
                    {"status": {"$in": ["pending", "", "completed"]}} 
                ],
            },
            {"_id": 1}  # Fetch only required fields
            ).sort({ "last_crawled": 1 }).limit(num_of_urls))

        print(f"Found {len(urls_to_find)} URLs to lock.")

        if not urls_to_find:
            print("No more URLs to process.")
            return []

        url_ids = [url["_id"] for url in urls_to_find]  # Step 2: Extract IDs to update

        # Lock the URLs by updating their status and adding a process lock
        self.urls_collection.update_many(
        {
                "$and": [
                    { "_id": {"$in": url_ids} },
                    {"status": { "$ne": "processing" } }
                ]
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
            {"_id": 1,"url": 1, "domain_id": 1,"locked_by": 1}  
        ))

        for url_data in locked_url_find:
                self.process_url(url_data)


    def process_url(self, url):
        html_content,status_code = self.fetch_html(url["url"])
        if html_content:
            emails = Extractor.extract_email(html_content)
            names = Extractor.extract_names(html_content)
            extracted_links = Extractor.extract_links(html_content, url["url"])

            print(f"\nExtracted links from: {url['url']}")
            print("\n[Internal Links]")
            for link in extracted_links["internal"]:
                print(link)

            print("\n[External Links]")
            for link in extracted_links["external"]:
                print(link)
            self.store_extracted_links(extracted_links["internal"], url)
            self.store_extracted_links(extracted_links["external"], url)
            
              # Update the URL status to 'completed' after processing
            self.urls_collection.update_one(
                {"_id": url["_id"], "locked_by": url["locked_by"]},  # Ensure only the same process updates it
                {"$set": {
                    "last_crawled": datetime.now(UTC),
                    "status": "completed",
                    "locked_at": None,
                    "locked_by": None,
                    "html_content":html_content,
                    "Status_code":status_code,
                    "emails": list(set(emails)),
                    "company_names": names["organization"]
                }}
            )
            print(f" Successfully processed and completed URL: {url['url']}")
        else:
            print(f"Error processing URL {url['url']}")
            self.urls_collection.update_one(
                {"_id": url["_id"], "locked_by": url["locked_by"]},
                {"$set": {
                    "status": "completed",
                    "status_code": status_code,
                    "locked_at": None,
                    "locked_by": None
                }}
            )

    def store_extracted_links(self, extracted_links,url):
        domain_from_url = parse_domain(url["url"])
        
        for link in extracted_links:
            # Normalize the domain of the extracted link
            link_domain = parse_domain(link)

            # Determine if this is an internal link
            is_internal = (domain_from_url == link_domain)
            
            if is_internal:
                domain_id = url["domain_id"]
            else:
                # Look up the domain_id from the domain collection
                domain_doc = self.domains_collection.find_one({"normalized_domain": link_domain})
                domain_id = domain_doc["_id"] if domain_doc else 0

            link = link.strip() 
            link_hash = generate_md5(link)
            
            self.urls_collection.update_one(
                    {"md5_url":link_hash},   # Find by MD5 hash
                    {
                        "$setOnInsert": {
                            "md5_url": link_hash,
                            "url": link,
                            "domain_id": domain_id,
                        },
                    },
                    upsert=True  # This will insert the link if it's new
                )
            print(f" Link added: {link}.")