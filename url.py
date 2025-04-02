import socket
import requests
import os
from extractor import Extractor
from db_handler import DatabaseHandler
from datetime import datetime, timedelta, UTC
from utils import parse_domain, generate_md5


class URLHandler:
    #LOCK_TIMEOUT = timedelta(minutes=10)

    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.urls_collection = self.db_handler.db["urls"]

    def fetch_html(self, url):
        """Fetches the HTML content of a URL."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f" Error fetching {url}: {e}")
            return None

    def get_url_list_last_crawled_48hrs_before(self, num_of_urls=100):
        """Retrieve and lock URLs atomically to prevent duplicate pickups."""
        now = datetime.now(UTC)
        cutoff_time = now - timedelta(hours=48)
        process_id = f"crawler_{os.getpid()}"  # Unique identifier for the process
        hostname = socket.gethostname()

        urls_to_lock = list(self.urls_collection.find(
            {
                "$or": [
                    {"last_crawled": {"$lt": cutoff_time}},  # Older than 48 hours
                    {"last_crawled": {"$exists": False}},
                    {"status": {"$exists": False}},
                    {"status": "pending"},  # Always crawl "pending" URLs
                    {"status": ""},
                ],
            },
            {"_id": 1 }  # Fetch only required fields
            ).limit(num_of_urls))

        print(f"Found {len(urls_to_lock)} URLs to lock.")

        if not urls_to_lock:
            print("No more URLs to process.")
            return []

        url_ids = [url["_id"] for url in urls_to_lock]  # Step 2: Extract IDs to update

        # Lock the URLs by updating their status and adding a process lock
        self.urls_collection.update_many(
        {
            "_id": {"$in": url_ids},
            "$or": [
                {"status": {"$exists": False}},  # status doesn't exist
                {"status": {"$ne": "processing"}},  # status is not "processing"
                {"status": {"$in": ["", "pending"]}},  # status is either "" or "pending"
            ],
        },
            {
                "$set": {
                    "status": "processing",
                    "locked_at": now,
                    "locked_by": f"{hostname} + {process_id}",
                }
            }
        )

        urls_to_process = list(self.urls_collection.find(
        {
            "$or": [
                { "_id": {"$in": url_ids}},
                {"status": {"$exists": False}},
                {"status": "pending"},
                {"status": ""}
            ]
        },
        {"_id": 1, "url": 1, "status": 1, "locked_at": 1, "locked_by": 1, "domain_id": 1}
    ).limit(num_of_urls))

        for url_data in urls_to_process:
                self.process_url(url_data)

        self.urls_collection.update_many(
            {"_id": {"$in": url_ids}},
            {
                "$set": {
                    "status": "complete",
                    "locked_at": None,
                    "locked_by": None,
                    "last_crawled": now,
                }
            }
        )

    def process_url(self, url):
        html_content = self.fetch_html(url["url"])

        if html_content:
            extracted_links = Extractor.extract_links(html_content, url["url"])
            
            self.store_extracted_links(extracted_links,url)  # Store the extracted links in the database

              # Update the URL status to 'completed' after processing
            self.urls_collection.update_one(
                {"_id": url["_id"], "locked_by": url["locked_by"]},  # Ensure only the same process updates it
                {"$set": {
                    "last_crawled": datetime.now(UTC),
                    "status": "completed",
                    "locked_at": None,
                    "locked_by": None
                }}
            )
            print(f" Successfully processed and completed URL: {url['url']}")
        else:
            print(f"Error processing URL {url['url']}")
            self.urls_collection.update_one(
                {"_id": url["_id"], "locked_by": url["locked_by"]},
                {"$set": {
                    "status": "pending",
                    "locked_at": None,
                    "locked_by": None
                }}
            )
    def save_domain_url(self,url):
        "store the domain if it's not store"
        domain = parse_domain(url)

        if not domain:
            print("Invalid URL: {url}")
            return False
        
        #check if domains exist or not
        existing = self.db_handler.urls_collection.find_one({"domain": domain})
        if existing:
            print(f"Domain {domain} already exist. skipping....")
            return False
        
        #store new domain

        self.db_handler.urls_collection.insert_one({
            "domain": domain,
            "original_url": url
        })
        print(f"New domain added: {domain}")
        return True

    def store_extracted_links(self, extracted_links,url):
        domain_from_url = parse_domain(url["url"])
        

        for link in extracted_links:
            domain_id=0
            if domain_from_url in link:
                domain_id=url["domain_id"]

            link = link.strip() 
            link_hash = generate_md5(link)
            
            
            self.urls_collection.update_one(
                    {"md5_url":link_hash},   # Find by MD5 hash
                    {
                        "$setOnInsert": {
                            "md5_url": link_hash,
                            "url": link,
                            "domain_id": domain_id,
                            "locked_at": None,
                            "locked_by": None,
                        }
                    },
                    upsert=True  # This will insert the link if it's new
                )
            print(f" Link added: {link}.")

    
    

