#!/usr/bin/env python
"""
Script to initialize the MongoDB database with the required collections and indexes.
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variable
MONGO_URI = os.getenv("CRAWLER_DB_SERVER", "mongodb://localhost:27017/")
DB_NAME = os.getenv("CRAWLER_DB_NAME", "crawler")

def init_database():
    """Initializes the database with required collections and indexes."""
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Create domains collection if it doesn't exist
    if "domains" not in db.list_collection_names():
        db.create_collection("domains")
        print("Created 'domains' collection")
    
    # Create urls collection if it doesn't exist
    if "urls" not in db.list_collection_names():
        db.create_collection("urls")
        print("Created 'urls' collection")
    
    # Create indexes for domains collection
    domains = db["domains"]
    domains.create_index([("normalized_domain", ASCENDING)], unique=True)
    domains.create_index([("status", ASCENDING)])
    domains.create_index([("last_seen", DESCENDING)])
    print("Created indexes for 'domains' collection")
    
    # Create indexes for urls collection
    urls = db["urls"]
    urls.create_index([("md5_url", ASCENDING)], unique=True)
    urls.create_index([("url", ASCENDING)])
    urls.create_index([("domain_id", ASCENDING)])
    urls.create_index([("normalized_domain", ASCENDING)])
    urls.create_index([("status", ASCENDING)])
    urls.create_index([("last_crawled", ASCENDING)])
    print("Created indexes for 'urls' collection")
    
    print("Database initialization completed successfully!")

def main():
    """Main function to initialize the database."""
    init_database()

if __name__ == "__main__":
    main() 