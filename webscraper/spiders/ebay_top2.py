# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
from fake_headers import Headers
from pymongo import MongoClient

header = Headers(browser="chrome",  # Generate only Chrome UA
                 os="win",  # Generate only Windows platform
                 headers=True)

class EbayTop3(scrapy.Spider):
    name = 'ebay_top3'
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': True,  # Enable cookies to see if it helps
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

    def __init__(self, url=None, *args, **kwargs):
        super(EbayTop3, self).__init__(*args, **kwargs)
        self.url = url
        # Conexión a MongoDB con credenciales
        self.client = MongoClient('mongodb+srv://xavidb:WrwQeAALK5kTIMCg@serverlessinstance0.lih2lnk.mongodb.net/')
        self.db = self.client["Xavi_UK"]
        self.collection = self.db['Search_uk_E']

    def start_requests(self):
        df = pd.read_csv(self.url)
        url_list = [i for i in df['url'].tolist() if i.strip()]

        for request_url in url_list:
            try:
                nkw = request_url.split('_nkw=')[1].split('&')[0]
            except:
                nkw = ''
            yield scrapy.Request(url=request_url, callback=self.parse, headers=self.headers, 
                                 meta={'proxy': self.proxy, 'nkw': nkw})

    def parse(self, response):
        nkw = response.meta['nkw']
        listings = response.xpath('//ul//div[@class="s-item__wrapper clearfix"]')

        count = 0  # Initialize a counter for the number of listings processed

        for listing in listings:
            if listing.xpath('.//li[contains(@class,"srp-river-answer--REWRITE_START")]').get():
                self.logger.info("Found international sellers separator. Stopping extraction for this URL.")
                break

            # Skip listings that contain the specified location
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

            # Multiple XPath expressions for shipping cost
            shipping_cost = listing.xpath('.//span[contains(text(),"postage") or contains(text(),"shipping")]/text()').re_first(r'\+\s?[£$€][\d,.]+')
            if not shipping_cost:
                shipping_cost = listing.xpath('.//span[contains(@class,"s-item__shipping") or contains(@class,"s-item__logisticsCost") or contains(@class,"s-item__freeXDays")]/text()').re_first(r'\+\s?[£$€][\d,.]+')

            # Extract seller name
            seller_name = listing.xpath('.//span[@class="s-item__seller-info-text"]//text()').get('')
            if not seller_name:
                seller_name = listing.xpath('.//span[@class="s-item__seller-info"]//text()').get('')

            if seller_name:
                seller_name = seller_name.split('(')[0].strip()
                self.logger.info(f"Extracted seller name: {seller_name}")
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
            
            # Insert the item into MongoDB
            self.collection.insert_one(item)

            yield item

            count += 1  # Increment the counter

            # Stop processing after the first two listings without location info
            if count >= 2:
                break

    def close(self, reason):
        self.client.close()
