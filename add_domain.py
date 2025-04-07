#!/usr/bin/env python
"""
Script to add domains individually to the MongoDB database.
Usage: python add_domain.py domain_name [notes]
Example: python add_domain.py example.com "This is a test domain"
"""

import sys
import os
from datetime import datetime, UTC
from pymongo import MongoClient
from dotenv import load_dotenv
from domain import DomainHandler

# Load environment variables from .env file
load_dotenv()

def add_domain(domain_name, notes=None):
    """Adds a domain to the domains collection."""
    domain_handler = DomainHandler()
    domain_id = domain_handler.add_domain(domain_name, notes)
    
    if domain_id:
        print(f"Domain '{domain_name}' added with ID: {domain_id}")
    else:
        print(f"Failed to add domain '{domain_name}'")

def main():
    """Main function to add a domain."""
    if len(sys.argv) < 2:
        print("Usage: python add_domain.py domain_name [notes]")
        print("Example: python add_domain.py example.com \"This is a test domain\"")
        return
    
    domain_name = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else None
    
    add_domain(domain_name, notes)

if __name__ == "__main__":
    main() 