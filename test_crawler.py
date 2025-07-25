#!/usr/bin/env python3
"""
Test script for the Playwright-based Newsday crawler
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from newsday_crawler import NewsdayCrawler
import logging

logging.basicConfig(level=logging.INFO)

def test_single_date():
    """Test crawling a single date"""
    crawler = NewsdayCrawler(headless=False)
    
    # Test with a recent date
    from datetime import datetime, timedelta
    test_date = datetime.now() - timedelta(days=30)
    date_info = {
        'url': f"https://newsday.co.tt/{test_date.strftime('%Y/%m/%d')}/",
        'date': test_date.strftime('%Y-%m-%d')
    }
    
    print(f"Testing crawl for: {date_info['url']}")
    
    result = crawler.process_date_batch(date_info, delay=1.0)
    
    print(f"Found {len(crawler.articles_data)} articles")
    
    if crawler.articles_data:
        print("Sample article:")
        sample = crawler.articles_data[0]
        for key, value in sample.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")
    
    return len(crawler.articles_data)

def test_article_extraction():
    """Test direct article URL crawling"""
    crawler = NewsdayCrawler(headless=True)
    
    # Test with newsday.co.tt homepage to find recent articles
    test_url = "https://newsday.co.tt"
    
    print(f"Testing article extraction from: {test_url}")
    
    result = crawler.crawl_page(test_url)
    
    if result and result.get('articles'):
        print(f"Found {len(result['articles'])} article links")
        
        # Test full content extraction on first article
        if result['articles']:
            first_article = result['articles'][0]
            print(f"Testing full content extraction for: {first_article.get('url', 'No URL')}")
            
            if first_article.get('url'):
                full_content = crawler.crawl_article_content(first_article['url'])
                if full_content:
                    print("Full content extraction successful!")
                    print(f"Title: {full_content.get('title', 'N/A')}")
                    print(f"Author: {full_content.get('author', 'N/A')}")
                    print(f"Content preview: {str(full_content.get('content', 'N/A'))[:200]}...")
                else:
                    print("Full content extraction failed")
    else:
        print("No articles found")

if __name__ == "__main__":
    print("=== Testing Playwright Newsday Crawler ===")
    
    print("\n1. Testing single date crawling...")
    try:
        test_single_date()
    except Exception as e:
        print(f"Single date test failed: {e}")
    
    print("\n2. Testing article extraction...")
    try:
        test_article_extraction()
    except Exception as e:
        print(f"Article extraction test failed: {e}")
    
    print("\nTest completed!")