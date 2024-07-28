import re
import scrapy
from datetime import datetime, timedelta
from pymongo import MongoClient
from fake_headers import Headers
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError

header = Headers(browser="chrome", os="win", headers=True)

class EbayTop2Spider(scrapy.Spider):
    name = 'ebay_top2'
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0,
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': "utf-8",
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
            'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None,
            'webscraper.middlewares.CustomRetryMiddleware': 550,
        },
        'AUTOTHROTTLE_ENABLED': False,
        'ITEM_PIPELINES': {
            'webscraper.pipelines.MongoDBPipeline': 300,
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

    proxy = 'http://xavigv:e8qcHlJ5jdHxl7Xj_country-UnitedKingdom@proxy.packetstream.io:31112'

    def __init__(self, *args, **kwargs):
        super(EbayTop2Spider, self).__init__(*args, **kwargs)
        self.connect()

    def connect(self):
        try:
            self.logger.info("Attempting to connect to MongoDB...")
            client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/Xavi_UK?retryWrites=true&w=majority')
            self.db = client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            self.collection_A = self.db['Search_uk_A']
            self.collection_cache = self.db['Search_uk_Cache']
            self.logger.info("Connected to MongoDB.")
        except Exception as e:
            self.logger.error(f"Error connecting to MongoDB: {e}")

import re
import scrapy
from datetime import datetime, timedelta
from pymongo import MongoClient
from fake_headers import Headers
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError

header = Headers(browser="chrome", os="win", headers=True)

class EbayTop2Spider(scrapy.Spider):
    name = 'ebay_top2'
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0,
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': "utf-8",
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
            'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None,
            'webscraper.middlewares.CustomRetryMiddleware': 550,
        },
        'AUTOTHROTTLE_ENABLED': False,
        'ITEM_PIPELINES': {
            'webscraper.pipelines.MongoDBPipeline': 300,
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

    proxy = 'http://xavigv:e8qcHlJ5jdHxl7Xj_country-UnitedKingdom@proxy.packetstream.io:31112'

    def __init__(self, *args, **kwargs):
        super(EbayTop2Spider, self).__init__(*args, **kwargs)
        self.connect()

    def connect(self):
        try:
            self.logger.info("Attempting to connect to MongoDB...")
            client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/Xavi_UK?retryWrites=true&w=majority')
            self.db = client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            self.collection_A = self.db['Search_uk_A']
            self.collection_cache = self.db['Search_uk_Cache']
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
            reference_number = data_urls_loop.get('reference_number', '')

            if url:
                self.logger.info(f"Creating request for URL: {url}")
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    headers=self.headers,
                    meta={'_id': data_urls_loop['_id'], 'proxy': self.proxy, 'reference_number': reference_number},
                    errback=self.errback_httpbin
                )
            else:
                self.logger.warning("Empty URL found in the Search_uk_E collection.")


    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
            if response.status == 503:
                self.logger.warning('503 Service Unavailable on %s', response.url)
                time.sleep(60)  # Wait for 60 seconds before retrying
                return scrapy.Request(response.url, callback=self.parse, dont_filter=True, headers=self.headers, meta={'proxy': self.proxy})
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def parse(self, response):
        _id = response.meta.get('_id')
        reference_number = response.meta.get('reference_number')
        self.logger.info(f"Processing response for _id: {_id} and reference_number: {reference_number}")
        listings = response.xpath('//ul//div[@class="s-item__wrapper clearfix"]')

        count = 0

        for listing in listings:
            if listing.xpath('.//li[contains(@class,"srp-river-answer--REWRITE_START")]').get():
                self.logger.info("Found international sellers separator. Stopping extraction for this URL.")
                break

            if listing.xpath('.//span[@class="s-item__location s-item__itemLocation"]').get():
                self.logger.info("Skipping listing with location info.")
                continue

            link = listing.xpath('.//a[@class="s-item__link"]/@href').get('')
            title = listing.xpath('.//span[@role="heading"]/text()').get('')
            price = listing.xpath('.//span[@class="s-item__price"]/text()').get('')
            if not price:
                price = listing.xpath('.//span[@class="s-item__price"]/span/text()').get('')

            image = listing.xpath('.//div[contains(@class,"s-item__image")]//img/@src').get('')
            image = image.replace('s-l225.webp', 's-l500.jpg')

            shipping_cost = listing.xpath('.//span[contains(text(),"postage") or contains(text(),"shipping")]/text()').re_first(r'\+\s?[£$€][\d,.]+')
            if not shipping_cost:
                shipping_cost = listing.xpath('.//span[contains(@class,"s-item__shipping") or contains(@class,"s-item__logisticsCost") or contains(@class,"s-item__freeXDays")]/text()').re_first(r'\+\s?[£$€][\d,.]+')

            if not shipping_cost:
                shipping_cost = '0.0'

            # Extract the item number
            try:
                item_number = link.split('/itm/')[1].split('?')[0]
            except:
                item_number = ''

            self.logger.info(f"Extracted data - Link: {link}, Title: {title}, Price: {price}, Image: {image}, Shipping Cost: {shipping_cost}, Item Number: {item_number}")

            item = {
                'image_url': image,
                'product_title': title,
                'product_price': price,
                'shipping_fee': shipping_cost,
                'item_number': item_number,
                'product_url': link,
                '_id': _id,
                'reference_number': reference_number,
            }

            count += 1
            self.logger.info(f"Inserting item {count} into MongoDB: {item}")
            self.collection_cache.update_one(
                {'_id': _id},
                {'$set': item},
                upsert=True
            )

            if count == 2:
                self.logger.info(f"Extracted {count} items, stopping extraction for this URL.")
                break

        if count == 0:
            self.logger.warning(f"No valid listings found for _id: {_id}")

        def errback_httpbin(self, failure):
            self.logger.error(repr(failure))
            if failure.check(HttpError):
                response = failure.value.response
                self.logger.error('HttpError on %s', response.url)
                if response.status == 503:
                    self.logger.warning('503 Service Unavailable on %s', response.url)
                    time.sleep(60)  # Wait for 60 seconds before retrying
                    return scrapy.Request(response.url, callback=self.parse, dont_filter=True, headers=self.headers, meta={'proxy': self.proxy})
            elif failure.check(DNSLookupError):
                request = failure.request
                self.logger.error('DNSLookupError on %s', request.url)
            elif failure.check(TimeoutError, TCPTimedOutError):
                request = failure.request
                self.logger.error('TimeoutError on %s', request.url)
