#!/usr/bin/env python
"""
Script to add a seed URL to start the crawling process.
Usage: python add_seed_url.py url [domain_id]
Example: python add_seed_url.py https://example.com
"""

import sys
import os
from datetime import datetime, UTC
from pymongo import MongoClient
from dotenv import load_dotenv
from utils import normalize_url, parse_domain, generate_md5
from domain import DomainHandler

# Load environment variables from .env file
load_dotenv()

def add_seed_url(url, domain_id=None):
    """Adds a seed URL to the urls collection."""
    # Connect to MongoDB
    client = MongoClient(os.getenv("CRAWLER_DB_SERVER", "mongodb://localhost:27017/"))
    db = client[os.getenv("CRAWLER_DB_NAME", "crawler")]
    urls_collection = db["urls"]
    
    # Normalize the URL
    normalized_url = normalize_url(url)
    
    # Get the normalized domain
    normalized_domain = parse_domain(normalized_url)
    
    # If domain_id is not provided, try to find it in the domains collection
    if domain_id is None:
        domain_handler = DomainHandler()
        domain_id = domain_handler.add_domain(normalized_domain)
    
    # Generate MD5 hash for the URL
    url_hash = generate_md5(normalized_url)
    
    # Check if URL already exists
    existing_url = urls_collection.find_one({"md5_url": url_hash})
    
    if existing_url:
        print(f"URL '{normalized_url}' already exists with ID: {existing_url['_id']}")
        return existing_url["_id"]
    
    # Create new URL document
    now = datetime.now(UTC)
    url_doc = {
        "md5_url": url_hash,
        "url": normalized_url,
        "domain_id": domain_id,
        "normalized_domain": normalized_domain,
        "discovered_at": now,
        "last_updated": now,
        "status": "pending"
    }
    
    # Insert the URL
    result = urls_collection.insert_one(url_doc)
    
    print(f"Added seed URL '{normalized_url}' with ID: {result.inserted_id}")
    return result.inserted_id

def main():
    """Main function to add a seed URL."""
    if len(sys.argv) < 2:
        print("Usage: python add_seed_url.py url [domain_id]")
        print("Example: python add_seed_url.py https://example.com")
        return
    
    url = sys.argv[1]
    domain_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    add_seed_url(url, domain_id)

if __name__ == "__main__":
    main() 