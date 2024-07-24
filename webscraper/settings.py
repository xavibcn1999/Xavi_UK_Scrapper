# webscraper/settings.py

import datetime  # Asegúrate de importar datetime

BOT_NAME = 'webscraper'

SPIDER_MODULES = ['webscraper.spiders']
NEWSPIDER_MODULE = 'webscraper.spiders'

# Configuración de MongoDB
MONGO_URI = 'mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/Xavi_UK?retryWrites=true&w=majority'
MONGO_DATABASE = 'Xavi_UK'
MONGO_COLLECTION_E = 'Search_uk_E'
MONGO_COLLECTION_A = 'Search_uk_A'

# Configurar pipelines de ítems
ITEM_PIPELINES = {
    'webscraper.pipelines.MongoDBPipeline': 300,
}

# Middlewares del downloader
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None,
    'webscraper.middlewares.CustomRetryMiddleware': 550,
}

# Configuración de AutoThrottle
AUTOTHROTTLE_ENABLED = False  # Desactivar AutoThrottle para máxima velocidad

# Otras configuraciones
CONCURRENT_REQUESTS = 16  # Aumentar concurrencia
DOWNLOAD_DELAY = 0  # Sin demora para máxima velocidad
RETRY_TIMES = 15  # Aumentar el número de reintentos
COOKIES_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"
FEED_FORMAT = 'csv'
FEED_URI = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv'
