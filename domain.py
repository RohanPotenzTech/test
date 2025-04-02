from db_handler import DatabaseHandler

class DomainHandler:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.domains_collection = self.db_handler.db["domains"]

    def get_domain_list(self):
        """Retrieve all domains with their IDs and URLs."""
        return list(self.domains_collection.find({}, {"_id": 1, "url": 1}))
    

if __name__ == "__main__":
    domain_handler = DomainHandler()
    print("✅ Domain list:", domain_handler.get_domain_list())






    