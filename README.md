# Newsday.co.tt Crawler

A Python crawler using Playwright to collect historical articles from newsday.co.tt going back 15 years.

## Setup

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Run the crawler
python newsday_crawler.py
```

### Programmatic Usage
```python
from newsday_crawler import NewsdayCrawler

# Initialize crawler
crawler = NewsdayCrawler(headless=True)

# Crawl 15 years of data (default)
crawler.crawl_historical_data(years_back=15, max_workers=2, delay=0.5)

# Save results
results = crawler.save_data()
print(f"Collected {results['total_articles']} articles")
```

## Features

- **Historical crawling**: Goes back 15 years from current date
- **Date-based URL generation**: Creates URLs for each day based on newsday.co.tt's URL structure
- **Full article content**: Extracts complete article text using Playwright browser automation
- **Multiple output formats**: Saves data as JSON, CSV, and Excel files
- **Rate limiting**: Configurable delays between requests
- **Error handling**: Retry logic for failed requests
- **Progress tracking**: Shows progress with tqdm progress bars
- **Concurrent processing**: Uses ThreadPoolExecutor for faster crawling
- **Robust parsing**: Uses BeautifulSoup for reliable HTML parsing

## Output

The crawler saves data in three formats:
- **JSON**: Complete structured data with all fields
- **CSV**: Tabular format for easy analysis
- **Excel**: Formatted spreadsheet with all data

### Data Fields
- `title`: Article headline
- `content`: Full article text
- `author`: Article author
- `date`: Publication date
- `category`: Article category/section
- `url`: Original article URL
- `crawl_date`: Date when article was crawled
- `source_url`: Source page URL where article was found
- `tags`: Article tags (if available)

## Customization

### Adjust crawling period
```python
# Crawl only 5 years back
crawler.crawl_historical_data(years_back=5)
```

### Change delay between requests
```python
# 1 second delay between requests
crawler.crawl_historical_data(delay=1.0)
```

### Run in non-headless mode (for debugging)
```python
# Show browser window
crawler = NewsdayCrawler(headless=False)
```

## Rate Limits

The crawler includes rate limiting to be respectful to the newsday.co.tt servers. Default delay is 0.5 seconds between requests. Adjust based on your needs and server response times.

## Error Handling

- Automatic retries for failed requests (up to 3 attempts)
- Exponential backoff for retry delays
- Detailed logging of errors and progress
- Graceful handling of missing or malformed data