from db_handler import DatabaseHandler
from datetime import datetime, UTC
from utils import parse_domain

class DomainHandler:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.domains_collection = self.db_handler.domains_collection

    def get_domain_list(self):
        """Retrieve all domains with their IDs and normalized domains."""
        return list(self.domains_collection.find({}, {"_id": 1, "normalized_domain": 1, "status": 1}))
    
    def get_domain_by_id(self, domain_id):
        """Retrieve a domain by its ID."""
        return self.domains_collection.find_one({"_id": domain_id})
    
    def get_domain_by_name(self, domain_name):
        """Retrieve a domain by its normalized name."""
        normalized_domain = parse_domain(domain_name)
        return self.domains_collection.find_one({"normalized_domain": normalized_domain})
    
    def update_domain_status(self, domain_id, status):
        """Update the status of a domain."""
        now = datetime.now(UTC)
        result = self.domains_collection.update_one(
            {"_id": domain_id},
            {
                "$set": {
                    "status": status,
                    "last_seen": now
                }
            }
        )
        return result.modified_count > 0
    
    def add_domain(self, domain_name, notes=None):
        """Add a new domain to the database."""
        normalized_domain = parse_domain(domain_name)
        
        # Check if domain already exists
        existing_domain = self.domains_collection.find_one({"normalized_domain": normalized_domain})
        
        if existing_domain:
            return existing_domain["_id"]
        
        # Create new domain document
        now = datetime.now(UTC)
        domain_doc = {
            "normalized_domain": normalized_domain,
            "first_seen": now,
            "last_seen": now,
            "status": "active"
        }
        
        # Add notes if provided
        if notes:
            domain_doc["notes"] = notes
        
        # Insert the domain
        result = self.domains_collection.insert_one(domain_doc)
        
        return result.inserted_id


if __name__ == "__main__":
    domain_handler = DomainHandler()
    print("✅ Domain list:", domain_handler.get_domain_list())






    