from url import URLHandler

def main():
    """Main function to manage crawling process."""
    url_handler = URLHandler()
    
    # Process URLs older than 48 hours
    url_handler.get_url_list_last_crawled_48hrs_before(100)
    print("Crawling process completed.")

if __name__ == "__main__":
        main()