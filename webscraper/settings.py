# webscraper/settings.py

BOT_NAME = 'webscraper'

SPIDER_MODULES = ['webscraper.spiders']
NEWSPIDER_MODULE = 'webscraper.spiders'

# Configure item pipelines
ITEM_PIPELINES = {
    'webscraper.pipelines.MongoDBPipeline': 300,
}

# Downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None,
    'webscraper.middlewares.CustomRetryMiddleware': 550,  # Ensure this is correct
}

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True

# Other settings
CONCURRENT_REQUESTS = 2
DOWNLOAD_DELAY = 5
RETRY_TIMES = 5
COOKIES_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"

# MongoDB settings (these are used in your custom pipeline)
MONGODB_URI = 'mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/'
MONGODB_DATABASE = 'Xavi_UK'
MONGODB_COLLECTION = 'Search_uk_E'
