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
            return  response.text,response.status_code

        except requests.RequestException as e:
            print(f" Error fetching {url}: {e}")
            return None

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
                    {"last_crawled": {"$lt": cutoff_time}},  #  Not crawled in 48+ hours
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

        url_ids = [url["_id"] for url in urls_to_find]  # Step 2: Extract IDs to update

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

            {"_id": 1,"url": 1, "domain_id": 1 }  
        ))

        for url_data in locked_url_find:
                url_data["locked_by"] = locked_by
                self.process_url(url_data)

    def process_url(self, url):
        html_content,status_code = self.fetch_html(url["url"])
        emails = Extractor.extract_email(html_content)
        names = Extractor.extract_names(html_content)

        if html_content:
            extracted_links = Extractor.extract_links(html_content, url["url"])
            self.store_extracted_links(extracted_links,url)  # Store the extracted links in the database

              # Update the URL status to 'completed' after processing
            self.urls_collection.update_many(
                {"_id": url["_id"], "locked_by": url["locked_by"]},  # Ensure only the same process updates it
                {"$set": {
                    "last_crawled": datetime.now(UTC),
                    "status": "completed",
                    "locked_at": None,
                    "locked_by": None,
                    "html_content":html_content,
                    "Status_code":status_code,
                    "emails": list(set(emails)),
                    "person_names":names["person_names"],
                    "company_names": names["company_names"]
                }}
            )
            print(f" Successfully processed and completed URL: {url['url']}")
        else:
            print(f"Error processing URL {url['url']}")
            self.urls_collection.update_one(
                {"_id": url["_id"], "locked_by": url["locked_by"]},
                {"$set": {
                    "status": "complete",
                    "status_code": status_code,
                    "locked_at": None,
                    "locked_by": None
                }}
            )

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
                            
                        },
                        "$set": {
                           
                        }
                    },
                    upsert=True  # This will insert the link if it's new
                )
            print(f" Link added: {link}.")