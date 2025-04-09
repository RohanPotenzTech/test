import pymongo
from datetime import datetime, timedelta, UTC
from db_config import MONGO_URI, DB_NAME
from  hashlib import md5

class DatabaseHandler:
    def __init__(self):
        try:
            self.client = pymongo.MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.domains_collection = self.db["domains"]
            self.urls_collection = self.db["urls"]

            existing_indexes = self.urls_collection.index_information()
            if "url_1" in existing_indexes:
                self.urls_collection.drop_index("url_1")

                    # Create a new unique index on `md5_url`
            self.urls_collection.create_index("md5_url", unique=True)
            
        except pymongo.errors.ConnectionFailure as e:
            print(f"❌ Could not connect to MongoDB: {e}")
            exit()

    