import scrapy
from pymongo import MongoClient
from datetime import datetime
from fake_headers import Headers

header = Headers(browser="chrome", os="win", headers=True)

class EbayTop2Spider(scrapy.Spider):
    name = 'ebay_top2'
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv',
        'RETRY_TIMES': 20,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': "utf-8",
        'DOWNLOAD_TIMEOUT': 30,
        'AUTOTHROTTLE_ENABLED': True,
        'DOWNLOAD_DELAY': 5,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
            'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 2,
        }
    }

    headers = {
        'authority': 'www.ebay.com',
        'upgrade-insecure-requests': '1',
        'user-agent': header.generate()['User-Agent'],
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-gpc': '1',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9',
    }

    def __init__(self, *args, **kwargs):
        super(EbayTop2Spider, self).__init__(*args, **kwargs)
        self.connect()

    def connect(self):
        try:
            client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/')
            self.db = client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            self.collection_A = self.db['Search_uk_A']
            self.logger.info("Conexión a MongoDB establecida.")
        except Exception as e:
            self.logger.error(f"Error al conectar a MongoDB: {e}")

    def start_requests(self):
        data_urls = list(self.collection_E.find({'url': {'$ne': ''}}))

        if not data_urls:
            self.logger.warning("No se encontraron URLs en la colección Search_uk_E.")
            return

        self.logger.info(f"Se encontraron {len(data_urls)} URLs para procesar.")

        for data_urls_loop in data_urls:
            url = data_urls_loop.get('url', '').strip()
            nkw = data_urls_loop.get('ASIN', '').strip("'")

            if url:
                self.logger.info(f"Generando solicitud para URL: {url}")
                yield scrapy.Request(
                    url=url, 
                    callback=self.parse, 
                    headers=self.headers,
                    meta={
                        'proxy': "http://xavigv:e8qcHlJ5jdHxl7Xj_country-UnitedKingdom@proxy.packetstream.io:31112",
                        'nkw': nkw
                    }
                )
            else:
                self.logger.warning("URL vacía encontrada en la colección Search_uk_E.")

    def parse(self, response):
        nkw = response.meta['nkw']
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

            self.collection_E.update_one(
                {'ASIN': nkw},
                {'$set': {
                    'Image URL': image,
                    'Product Title': title,
                    'Product Price': price,
                    'Shipping Fee': shipping_cost,
                }}
            )

            count += 1

            if count >= 2:
                break
