# Scrapy settings for webscraper project

BOT_NAME = 'webscraper'

SPIDER_MODULES = ['webscraper.spiders']
NEWSPIDER_MODULE = 'webscraper.spiders'

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

SPIDER_MIDDLEWARES = {
    'webscraper.middlewares.WebscraperSpiderMiddleware': 543,
}

DOWNLOADER_MIDDLEWARES = {
    'webscraper.middlewares.WebscraperDownloaderMiddleware': 543,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 30

INPUT_FILE = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQtb-UKr49Cj5tAof845aBQnN6Z_fnfaeGvvfKjee-XWz2OmNFlqW-XkItXUkhjEt7Xnr50yGdu_wcC/pub?output=csv'
