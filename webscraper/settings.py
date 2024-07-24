# webscraper/settings.py

import datetime  # Make sure to import datetime

BOT_NAME = 'webscraper'

SPIDER_MODULES = ['webscraper.spiders']
NEWSPIDER_MODULE = 'webscraper.spiders'

# MongoDB settings
MONGO_URI = 'mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/Xavi_UK?retryWrites=true&w=majority'
MONGO_DATABASE = 'Xavi_UK'
MONGODB_COLLECTION = 'Search_uk_E'

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
AUTOTHROTTLE_ENABLED = False  # Disable AutoThrottle for maximum speed

# Other settings
CONCURRENT_REQUESTS = 16  # Increased concurrency
DOWNLOAD_DELAY = 0  # No download delay for maximum speed
RETRY_TIMES = 15  # Increased retry times
COOKIES_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"
FEED_FORMAT = 'csv'
FEED_URI = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv'
