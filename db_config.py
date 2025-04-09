import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Environment Variables for MongoDB Connection
MONGO_URI = os.getenv("CRAWLER_DB_SERVER")
DB_NAME = os.getenv("CRAWLER_DB_NAME")
