# utils/web_scraper.py

import requests
from bs4 import BeautifulSoup

def scrape_website_text(url: str) -> tuple[str | None, str | None]:
    """
    Scrapes the main text content and title from a given website URL.

    Args:
        url: The URL of the website to scrape.

    Returns:
        A tuple containing (scraped_text, page_title) on success,
        or (None, error_message) on failure.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Remove non-content tags ---
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # --- Extract title ---
        page_title = soup.title.string if soup.title else "Scraped Note"

        # --- Extract main text ---
        # A common strategy is to look for the main content containers
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if main_content:
            # Get text from all relevant tags within the main content
            text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
            text = "\n".join(element.get_text(strip=True) for element in text_elements)
        else:
            text = soup.get_text(separator='\n', strip=True)

        if not text:
            return None, "Could not find any text content on the page."

        return text, page_title

    except requests.exceptions.RequestException as e:
        return None, f"Network error: Could not access the URL. {e}"
    except Exception as e:
        return None, f"An error occurred during scraping: {e}"
