# Web Crawler

A web crawler that extracts links, emails, and organization names from websites.

## Features

- Extracts internal and external links from web pages
- Extracts email addresses from web pages
- Extracts organization names from web pages
- Stores data in MongoDB for easy querying
- Handles domain normalization for consistent data
- Prevents duplicate URLs using MD5 hashing

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```
   python -m playwright install
   ```

3. Create a `.env` file with the following content:
   ```
   CRAWLER_DB_SERVER=mongodb://localhost:27017/
   CRAWLER_DB_NAME=crawler
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

## Usage

### Adding Domains

To add a domain to the database:
```
python add_domain.py example.com "Optional notes about the domain"
```

### Adding Seed URLs

To add a seed URL to start the crawling process:
```
python add_seed_url.py https://example.com
```

### Running the Crawler

To start the crawler:
```
python main.py
```

This will process URLs that haven't been crawled in the last 48 hours.

## Database Schema

### Domains Collection

```
{
  "_id": ObjectId,
  "normalized_domain": "example.com",
  "first_seen": ISODate,
  "last_seen": ISODate,
  "status": "active",
  "notes": "Optional notes"
}
```

### URLs Collection

```
{
  "_id": ObjectId,
  "md5_url": "md5_hash_of_url",
  "url": "https://example.com/page",
  "domain_id": ObjectId,
  "normalized_domain": "example.com",
  "source_url": "https://example.com",
  "discovered_at": ISODate,
  "last_updated": ISODate,
  "last_crawled": ISODate,
  "status": "completed",
  "html_content": "HTML content",
  "status_code": 200,
  "emails": ["email1@example.com", "email2@example.com"],
  "company_names": ["Example Corp", "Example Inc"]
}
```

## Project Structure

- `main.py`: Main script to run the crawler
- `url.py`: URL handler for fetching and processing URLs
- `extractor.py`: Extracts links, emails, and organization names from HTML
- `utils.py`: Utility functions for URL and domain handling
- `db_handler.py`: Database handler for MongoDB operations
- `db_config.py`: Database configuration
- `domain.py`: Domain handler for domain operations
- `init_db.py`: Initializes the database with required collections and indexes
- `add_domain.py`: Adds a domain to the database
- `add_seed_url.py`: Adds a seed URL to start the crawling process