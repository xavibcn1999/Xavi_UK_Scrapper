import scrapy
from pymongo import MongoClient
from datetime import datetime
from fake_headers import Headers
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError

header = Headers(browser="chrome", os="win", headers=True)

class EbayTop2Spider(scrapy.Spider):
    name = 'ebay_top2'
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 5,
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv',
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': "utf-8",
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
            'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None,
            'webscraper.middlewares.CustomRetryMiddleware': 550,  # Asegúrate de que este es el camino correcto
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'ITEM_PIPELINES': {
            'scrapy.pipelines.files.FilesPipeline': 1,  # Built-in pipeline for saving files
            'webscraper.pipelines.MongoDBPipeline': 300  # Custom pipeline for MongoDB
        }
    }

    headers = {
        'User-Agent': header.generate()['User-Agent'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

    def __init__(self, *args, **kwargs):
        super(EbayTop2Spider, self).__init__(*args, **kwargs)
        self.connect()

    def connect(self):
        try:
            self.logger.info("Attempting to connect to MongoDB...")
            client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/')
            self.db = client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            self.collection_A = self.db['Search_uk_A']
            self.logger.info("Connected to MongoDB.")
        except Exception as e:
            self.logger.error(f"Error connecting to MongoDB: {e}")

    def start_requests(self):
        self.logger.info("Fetching URLs from the Search_uk_E collection...")
        try:
            data_urls = list(self.collection_E.find({'url': {'$ne': ''}}))
            self.logger.info(f"Found {len(data_urls)} URLs to process.")
        except Exception as e:
            self.logger.error(f"Error fetching URLs from MongoDB: {e}")
            data_urls = []

        if not data_urls:
            self.logger.warning("No URLs found in the Search_uk_E collection.")
            return

        for data_urls_loop in data_urls:
            url = data_urls_loop.get('url', '').strip()
            nkw = data_urls_loop.get('ASIN', '').strip("'")

            if url:
                self.logger.info(f"Creating request for URL: {url} and ASIN: {nkw}")
                yield scrapy.Request(url=url, callback=self.parse, headers=self.headers,
                                     meta={'nkw': nkw}, errback=self.errback_httpbin)
            else:
                self.logger.warning("Empty URL found in the Search_uk_E collection.")

    def parse(self, response):
        nkw = response.meta.get('nkw', 'N/A')
        self.logger.info(f"Processing response for ASIN: {nkw}")
        listings = response.xpath('//ul//div[@class="s-item__wrapper clearfix"]')

        count = 0

        for listing in listings:
            if listing.xpath('.//li[contains(@class,"srp-river-answer--REWRITE_START")]').get():
                self.logger.info("Found international sellers separator. Stopping extraction for this URL.")
                break

            if listing.xpath('.//span[@class="s-item__location s-item__itemLocation"]').get():
                self.logger.info("Skipping listing with location info.")
                continue

            link = listing.xpath('.//a/@href').get('')
            title = listing.xpath('.//span[@role="heading"]/text()').get('')
            price = listing.xpath('.//span[@class="s-item__price"]/text()').get('')
            if not price:
                price = listing.xpath('.//span[@class="s-item__price"]/span/text()').get('')

            image = listing.xpath('.//div[contains(@class,"s-item__image")]//img/@src').get('')
            image = image.replace('s-l225.webp', 's-l500.jpg')

            shipping_cost = listing.xpath('.//span[contains(text(),"postage") or contains(text(),"shipping")]/text()').re_first(r'\+\s?[£$€][\d,.]+')
            if not shipping_cost:
                shipping_cost = listing.xpath('.//span[contains(@class,"s-item__shipping") or contains(@class,"s-item__logisticsCost") or contains(@class,"s-item__freeXDays")]/text()').re_first(r'\+\s?[£$€][\d,.]+')

            self.logger.info(f"Extracted data - Link: {link}, Title: {title}, Price: {price}, Image: {image}, Shipping Cost: {shipping_cost}")

            item = {
                'ASIN': nkw,
                'Image URL': image,
                'Product Title': title,
                'Product Price': price,
                'Shipping Fee': shipping_cost
            }

            yield item  # This will send the item to both the MongoDB pipeline and the CSV exporter

            count += 1

            if count >= 2:
                break

        if count == 0:
            self.logger.warning(f"No valid listings found for ASIN: {nkw}")

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
            if response.status == 503:
                self.logger.warning('503 Service Unavailable on %s', response.url)
                time.sleep(60)  # Wait for 60 seconds before retrying
                return scrapy.Request(response.url, callback=self.parse, dont_filter=True, headers=self.headers)
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

# Custom MongoDB pipeline
class MongoDBPipeline:

    def open_spider(self, spider):
        try:
            spider.logger.info("Opening MongoDB pipeline...")
            self.client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/')
            self.db = self.client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            spider.logger.info("MongoDB pipeline opened.")
        except Exception as e:
            spider.logger.error(f"Error connecting to MongoDB in pipeline: {e}")

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            update_result = self.collection_E.update_one(
                {'ASIN': item['ASIN']},
                {'$set': {
                    'Image URL': item['Image URL'],
                    'Product Title': item['Product Title'],
                    'Product Price': item['Product Price'],
                    'Shipping Fee': item['Shipping Fee']
                }},
                upsert=True
            )
            if update_result.modified_count > 0:
                spider.logger.info(f"Data updated for ASIN: {item['ASIN']}")
            elif update_result.upserted_id is not None:
                spider.logger.info(f"New document inserted for ASIN: {item['ASIN']}")
            else:
                spider.logger.warning(f"No document was updated or inserted for ASIN: {item['ASIN']}, the data might be the same.")
        except Exception as e:
            spider.logger.error(f"Error updating MongoDB for ASIN: {item['ASIN']} - {e}")
        return item
