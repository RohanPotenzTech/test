import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment Variables for MongoDB Connection
MONGO_URI = os.getenv("CRAWLER_DB_SERVER", "mongodb://localhost:27017/")
DB_NAME = os.getenv("CRAWLER_DB_NAME", "crawler")
