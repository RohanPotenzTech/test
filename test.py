from url import URLHandler  # make sure this is the correct path
import socket
import os
from playwright.sync_api import sync_playwright
from extractor import Extractor
from db_handler import DatabaseHandler
from datetime import datetime, timedelta, UTC
from utils import parse_domain, generate_md5

def fetch_html(self, url):
    try:
        redirect_chain = []
        final_url = None
        final_status = None
        html_content = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def handle_response(response):
                nonlocal final_url, final_status
                status = response.status
                resp_url = response.url

                if status in [301, 302, 303, 307, 308]:
                    redirect_chain.append({
                        "url": resp_url,
                        "status": status
                    })

                final_url = resp_url
                final_status = status

            page.on("response", handle_response)

            response = page.goto(url, timeout=30000, wait_until="networkidle")

            if response:
                final_status = response.status
                final_url = response.url
                redirect_chain.append({
                    "url": final_url,
                    "status": final_status
                })

            html_content = page.content()
            browser.close()

            return html_content, final_status, final_url, redirect_chain

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None, None, []
    


if __name__ == "__main__":
    url_handler = URLHandler()
    html, status, final_url, chain = url_handler.fetch_html("http://github.com")

    from pprint import pprint
    pprint({
        "status_code": status,
        "final_url": final_url,
        "redirect_chain": chain,
    })
