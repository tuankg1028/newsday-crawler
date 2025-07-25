#!/usr/bin/env python3
"""
Newsday.co.tt Crawler using Playwright
Crawls historical articles from newsday.co.tt going back 15 years
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsdayCrawler:
    def __init__(self, headless=False, user_agent=None):
        self.base_url = "https://newsday.co.tt"
        self.articles_data = []
        self.articles_lock = threading.Lock()
        self.headless = headless
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
    def generate_date_urls(self, years_back=15):
        """Generate URLs for date-based crawling"""
        end_date = datetime.now()
        start_date = end_date - relativedelta(years=years_back)
        
        urls = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y/%m/%d")
            url = f"{self.base_url}/{date_str}/"
            urls.append({
                'url': url,
                'date': current_date.strftime("%Y-%m-%d")
            })
            current_date += timedelta(days=1)
            
        return urls
    
    def crawl_page(self, url, max_retries=3):
        """Crawl a single page using Playwright"""
        for attempt in range(max_retries):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=self.headless)
                    context = browser.new_context(user_agent=self.user_agent)
                    page = context.new_page()
                    
                    # Navigate to the page
                    response = page.goto(url, wait_until='load', timeout=30000)

                    if response and response.status != 200:
                        logger.warning(f"HTTP {response.status} for {url}")
                        browser.close()
                        continue
                    
                    # Get page content
                    content = page.content()
                    browser.close()
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    articles = self.extract_articles_from_page(soup, url)
                    
                    return {'articles': articles}
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to crawl {url} after {max_retries} attempts")
                    return None
    
    def extract_articles_from_page(self, soup, page_url):
        """Extract articles from a date page using BeautifulSoup"""
        articles = []
        
        # Look for article links - adjust selectors based on newsday.co.tt structure
        article_links = soup.find_all('a', href=True)
        
        for link in article_links:
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            full_url = urljoin(self.base_url, href)
            
            # Filter for actual article URLs (adjust pattern as needed)
            if self.is_article_url(full_url):
                title = link.get_text(strip=True)
                if title and len(title) > 10:  # Filter out very short titles
                    articles.append({
                        'title': title,
                        'url': full_url,
                        'preview_text': title
                    })
        
        return articles
    
    def is_article_url(self, url):
        """Check if URL looks like an article URL"""
        # Adjust patterns based on newsday.co.tt URL structure
        article_patterns = [
            r'/\d{4}/\d{2}/\d{2}/.+',  # Date-based URLs
            r'/news/',
            r'/sports/',
            r'/features/',
            r'/editorial/',
            r'/entertainment/'
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def crawl_article_content(self, article_url):
        """Crawl full content of individual articles"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                
                response = page.goto(article_url, wait_until='load', timeout=30000)
                
                if response and response.status != 200:
                    browser.close()
                    return None
                
                content = page.content()
                browser.close()
                
                # Parse article content
                soup = BeautifulSoup(content, 'html.parser')
                article_data = self.extract_article_data(soup, article_url)
                
                return article_data
                
        except Exception as e:
            logger.error(f"Failed to crawl article {article_url}: {str(e)}")
            return None
    
    def extract_article_data(self, soup, url):
        """Extract structured data from article page"""
        data = {'url': url}
        
        # Extract title
        title_selectors = ['h1', '.headline', '.title', '[class*="title"]', '[class*="headline"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract content
        content_selectors = [
            '.article-content', '.entry-content', '.post-content', 
            '[class*="content"]', '.story-body', 'article'
        ]
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove script and style elements
                for script in content_elem(["script", "style"]):
                    script.decompose()
                data['content'] = content_elem.get_text(separator='\n', strip=True)
                break
        
        # Extract author
        author_selectors = ['.author', '.byline', '[class*="author"]', '[class*="byline"]']
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                data['author'] = author_elem.get_text(strip=True)
                break
        
        # Extract date
        date_selectors = ['.date', '.published', '[class*="date"]', 'time']
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                data['date'] = date_text
                break
        
        # Extract category
        category_selectors = ['.category', '.section', '[class*="category"]']
        for selector in category_selectors:
            cat_elem = soup.select_one(selector)
            if cat_elem:
                data['category'] = cat_elem.get_text(strip=True)
                break
        
        return data
    
    def process_date_batch(self, date_info, delay=0.5):
        """Process a single date URL"""
        try:
            result = self.crawl_page(date_info['url'])
            batch_articles = []
            
            if result and result.get('articles'):
                articles = result['articles']
                
                for article in articles:
                    article['crawl_date'] = date_info['date']
                    article['source_url'] = date_info['url']
                    
                    # Get full article content if URL is available
                    if article.get('url'):
                        full_content = self.crawl_article_content(article['url'])
                        if full_content:
                            article.update(full_content)
                        
                        # Small delay between article requests
                        time.sleep(0.1)
                    
                    batch_articles.append(article)
                
                # Thread-safe addition to main articles list
                with self.articles_lock:
                    self.articles_data.extend(batch_articles)
                    
                logger.info(f"Found {len(batch_articles)} articles for {date_info['date']}")
            
            # Rate limiting per thread
            time.sleep(delay)
            return len(batch_articles)
            
        except Exception as e:
            logger.error(f"Error processing {date_info['date']}: {str(e)}")
            return 0
    
    def crawl_historical_data(self, years_back=15, max_workers=2, delay=0.5):
        """Main method to crawl historical data with concurrent processing"""
        logger.info(f"Starting crawl for {years_back} years of data from newsday.co.tt")
        logger.info(f"Using {max_workers} concurrent workers")
        
        # Generate date URLs
        date_urls = self.generate_date_urls(years_back)
        logger.info(f"Generated {len(date_urls)} date URLs to crawl")
        
        # Process URLs concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_date = {
                executor.submit(self.process_date_batch, date_info, delay): date_info 
                for date_info in date_urls
            }
            
            # Track progress
            with tqdm(total=len(date_urls), desc="Crawling dates") as pbar:
                for future in as_completed(future_to_date):
                    date_info = future_to_date[future]
                    try:
                        article_count = future.result()
                        pbar.set_postfix({'articles': len(self.articles_data)})
                    except Exception as e:
                        logger.error(f"Error with {date_info['date']}: {str(e)}")
                    pbar.update(1)
    
    def save_data(self, filename_prefix="newsday_articles"):
        """Save crawled data to various formats"""
        if not self.articles_data:
            logger.warning("No data to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.articles_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.articles_data)} articles to {json_filename}")
        
        # Save as CSV
        df = pd.DataFrame(self.articles_data)
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        logger.info(f"Saved data to {csv_filename}")
        
        # Save as Excel
        excel_filename = f"{filename_prefix}_{timestamp}.xlsx"
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        logger.info(f"Saved data to {excel_filename}")
        
        return {
            'json': json_filename,
            'csv': csv_filename,
            'excel': excel_filename,
            'total_articles': len(self.articles_data)
        }

def main():
    """Main function to run the crawler"""
    try:
        # Initialize crawler with Playwright
        crawler = NewsdayCrawler(headless=True)

        # Crawl 15 years of data with 5 concurrent workers
        crawler.crawl_historical_data(years_back=15, max_workers=5, delay=0.5)
        
        # Save results
        results = crawler.save_data()
        
        print(f"\nCrawling completed!")
        print(f"Total articles collected: {results['total_articles']}")
        print(f"Files saved:")
        print(f"  - JSON: {results['json']}")
        print(f"  - CSV: {results['csv']}")
        print(f"  - Excel: {results['excel']}")
        
    except Exception as e:
        logger.error(f"Crawler failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()