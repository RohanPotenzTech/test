from url import URLHandler

def main():
    """Main function to manage crawling process."""
    url_handler = URLHandler()
    
    # Process URLs older than 48 hours
    urls_to_crawl = url_handler.get_url_list_last_crawled_48hrs_before(100)
    if urls_to_crawl:
        url_handler.process_url(urls_to_crawl)
    else:
        print("✅")

if __name__ == "__main__":
        main()
      
