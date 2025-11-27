import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import List, Dict, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KychubScraper:
    def __init__(self, base_url: str = "https://www.kychub.com/"):
        self.base_url = base_url
        self.visited_urls: Set[str] = set()
        self.scraped_content: List[Dict[str, str]] = []
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == urlparse(self.base_url).netloc

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        return " ".join(text.split())

    def extract_text_from_element(self, element) -> str:
        for script in element(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        text = element.get_text(separator=" ", strip=True)
        return self.clean_text(text)

    def scrape_page(self, url: str) -> Dict[str, str]:
        try:
            logger.info("Scraping: %s", url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else ""

            main_content = (
                soup.find("main") or soup.find("article") or soup.find("body")
            )
            content_text = (
                self.extract_text_from_element(main_content) if main_content else ""
            )

            meta_description = soup.find("meta", attrs={"name": "description"})
            description = (
                meta_description.get("content", "") if meta_description else ""
            )

            return {
                "url": url,
                "title": title_text,
                "content": content_text,
                "description": description,
            }
        except Exception as e:
            logger.error("Error scraping %s: %s", url, str(e))
            return None

    def find_internal_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            full_url = urljoin(current_url, href)

            if self.is_valid_url(full_url) and full_url not in self.visited_urls:
                parsed = urlparse(full_url)
                if not parsed.fragment:
                    links.append(full_url)

        return links

    def scrape_site(
        self, max_pages: int = 1, start_url: str = None
    ) -> List[Dict[str, str]]:
        start_url = start_url or self.base_url
        urls_to_visit = [start_url]

        while urls_to_visit and len(self.scraped_content) < max_pages:
            current_url = urls_to_visit.pop(0)

            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)

            try:
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "lxml")

                page_data = self.scrape_page(current_url)
                if page_data and page_data["content"]:
                    self.scraped_content.append(page_data)
                    logger.info(
                        "Successfully scraped: %s (%d chars)",
                        current_url,
                        len(page_data["content"]),
                    )

                new_links = self.find_internal_links(soup, current_url)
                urls_to_visit.extend(new_links[:10])

                time.sleep(1)

            except Exception as e:
                logger.error("Error processing %s: %s", current_url, str(e))
                continue

        logger.info(
            "Scraping complete. Total pages scraped: %d", len(self.scraped_content)
        )
        return self.scraped_content


def main():
    scraper = KychubScraper()
    content = scraper.scrape_site(max_pages=1)

    print(f"\nScraped {len(content)} pages")
    for item in content[:3]:
        print(f"\nURL: {item['url']}")
        print(f"Title: {item['title']}")
        print(f"Content length: {len(item['content'])} characters")


if __name__ == "__main__":
    main()
