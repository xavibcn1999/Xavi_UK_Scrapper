import scrapy
from pymongo import MongoClient
from datetime import datetime
from fake_headers import Headers
from urllib.parse import urlparse, urlunparse

header = Headers(browser="chrome",  # Generate only Chrome UA
                 os="win",  # Generate only Windows platform
                 headers=True)

class EbayTop2Spider(scrapy.Spider):
    name = 'ebay_top2'
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv',
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': "utf-8"
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

    proxy = 'http://xavigv:ee3ee0580b725494_country-UnitedKingdom@proxy.packetstream.io:31112'

    def __init__(self, *args, **kwargs):
        super(EbayTop2Spider, self).__init__(*args, **kwargs)
        self.connect()

    def connect(self):
        client = MongoClient('mongodb+srv://xavidb:WrwQeAALK5kTIMCg@serverlessinstance0.lih2lnk.mongodb.net/')
        self.db = client["Xavi_UK"]
        self.collection_A = self.db['Search_uk_A']
        self.collection_E = self.db['Search_uk_E']

    def start_requests(self):
        data_urls = list(self.collection_A.find({}))
        empty_url_count = 0

        for data_urls_loop in data_urls:
            url = data_urls_loop.get('URL', '').strip()
            nkw = data_urls_loop.get('NKW', '').strip("'")

            if not url:
                empty_url_count += 1
                self.logger.warning("Found an empty URL in the database.")
                continue

            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = urlunparse(parsed_url._replace(scheme='https'))

            if urlparse(url).hostname:
                yield scrapy.Request(url=url, callback=self.parse, headers=self.headers,
                                     meta={'proxy': self.proxy, 'nkw': nkw})
            else:
                empty_url_count += 1
                self.logger.warning(f"Invalid URL with no hostname: {url}")

        if empty_url_count > 0:
            self.logger.warning(f"Found {empty_url_count} empty or invalid URLs in the database.")

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

            seller_name = listing.xpath('.//span[@class="s-item__seller-info-text"]//text()').get('')
            if not seller_name:
                seller_name = listing.xpath('.//span[@class="s-item__seller-info"]//text()').get('')

            if seller_name:
                seller_name = seller_name.split('(')[0].strip()
            else:
                self.logger.warning(f"Could not extract seller name for listing: {link}")

            item = {
                'URL': response.url,
                'NKW': "'" + nkw,
                'Image URL': image,
                'Product Title': title,
                'Product Price': price,
                'Shipping Fee': shipping_cost,
                'Seller Name': seller_name,
            }

            self.collection_E.insert_one(item)

            count += 1

            if count >= 2:
                break

    def parse_product_details(self, response):
        pass
