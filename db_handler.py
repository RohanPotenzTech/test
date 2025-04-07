import pymongo
from datetime import datetime, timedelta, UTC
from db_config import MONGO_URI, DB_NAME
import hashlib

class DatabaseHandler:
    def __init__(self):
        try:
            self.client = pymongo.MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.domains_collection = self.db["domains"]
            self.urls_collection = self.db["urls"]

            # Ensure indexes exist
            self._ensure_indexes()
            
        except pymongo.errors.ConnectionFailure as e:
            print(f"❌ Could not connect to MongoDB: {e}")
            exit(1)
    
    def _ensure_indexes(self):
        """Ensure all required indexes exist."""
        # URLs collection indexes
        if "md5_url_1" not in self.urls_collection.index_information():
            self.urls_collection.create_index("md5_url", unique=True)
        
        if "url_1" not in self.urls_collection.index_information():
            self.urls_collection.create_index("url")
            
        if "domain_id_1" not in self.urls_collection.index_information():
            self.urls_collection.create_index("domain_id")
            
        if "normalized_domain_1" not in self.urls_collection.index_information():
            self.urls_collection.create_index("normalized_domain")
            
        if "status_1" not in self.urls_collection.index_information():
            self.urls_collection.create_index("status")
            
        if "last_crawled_1" not in self.urls_collection.index_information():
            self.urls_collection.create_index("last_crawled")
        
        # Domains collection indexes
        if "normalized_domain_1" not in self.domains_collection.index_information():
            self.domains_collection.create_index("normalized_domain", unique=True)
            
        if "status_1" not in self.domains_collection.index_information():
            self.domains_collection.create_index("status")
            
        if "last_seen_-1" not in self.domains_collection.index_information():
            self.domains_collection.create_index("last_seen", pymongo.DESCENDING)

    