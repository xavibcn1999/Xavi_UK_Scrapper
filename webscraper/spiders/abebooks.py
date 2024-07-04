# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
from fake_headers import Headers
import random
import time
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.http import HtmlResponse
from twisted.internet.error import TimeoutError, DNSLookupError
from scrapy.core.downloader.handlers.http11 import TunnelError

class AbebooksSpider(scrapy.Spider):
    name = 'abebooks'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,  # Incrementa el número de requests concurrentes
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'abebooks.csv',
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': False,
        'FEED_EXPORT_ENCODING': "utf-8",
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,  # Reduce el delay inicial de Autothrottle
        'AUTOTHROTTLE_MAX_DELAY': 30,  # Reduce el delay máximo de Autothrottle
        'DOWNLOAD_DELAY': random.uniform(1, 3),  # Reduce el rango de tiempo de delay
        'LOG_ENABLED': True,
        'LOG_LEVEL': 'INFO',
    }
    proxy_list = [
        'http://xavi1:hornh984y4pgvuu@proxy.packetstream.io:31112',
        'http://xavi2:r1w5fpk47hgqfgj@proxy.packetstream.io:31112',
        'http://xavi3:lo6vcj5ndrt7z2x@proxy.packetstream.io:31112',
        'http://xavi4:unw476v6wtysh96@proxy.packetstream.io:31112',
        'http://xavi5:d04lhxxisu82bzw@proxy.packetstream.io:31112',
        'http://xavi6:3wv0ha19gq7zdsd@proxy.packetstream.io:31112',
        'http://xavi7:iorvw43c052881o@proxy.packetstream.io:31112',
        'http://xavi8:9niv2y9y9ckiy7m@proxy.packetstream.io:31112',
        'http://xavi9:67x6so2sc8mzgv8@proxy.packetstream.io:31112',
        'http://xavi10:pbs51r030k4haoq@proxy.packetstream.io:31112'
    ]

    def __init__(self, url=None, *args, **kwargs):
        super(AbebooksSpider, self).__init__(*args, **kwargs)
        self.url = url

    def start_requests(self):
        df = pd.read_csv(self.url)
        url_list = [i for i in df['url'].tolist() if i.strip() and not i.startswith('#VALUE')]

        for request_url in url_list:
            headers = Headers(browser="chrome", os="win", headers=True).generate()
            proxy = random.choice(self.proxy_list)
            self.logger.info(f'Requesting URL: {request_url} with proxy: {proxy}')
            yield scrapy.Request(
                url=request_url,
                callback=self.parse,
                headers=headers,
                meta={'proxy': proxy},
                errback=self.errback_httpbin,
                dont_filter=True  # Permitir repetición de solicitudes
            )

    def parse(self, response):
        self.logger.info(f'Processing URL: {response.url}')
        if isinstance(response, HtmlResponse):
            listings = response.xpath('//li[@data-cy="listing-item"]')
            self.logger.info(f'Found {len(listings)} listings on {response.url}')

            for rank, listing in enumerate(listings[:3]):
                title = listing.xpath('.//span[@data-cy="listing-title"]/text()').get('')
                price = listing.xpath('.//meta[@itemprop="price"]/@content').get('')
                isbn = listing.xpath('.//meta[@itemprop="isbn"]/@content').get('')
                seller_name = listing.xpath('.//a[@data-cy="listing-seller-link"]/text()').get('')
                shipping_cost = listing.xpath('.//span[contains(@id,"item-shipping-price-")]/text()').get('')
                image = listing.xpath('.//div[@data-cy="listing-image"]/img/@src').get('')

                self.logger.info(f'Listing found: {title} - {price} - {isbn} - {seller_name} - {shipping_cost} - {image}')
                yield {
                    'URL': response.url,
                    'Image URL': image,
                    'Product Title': title,
                    'Product Price': price,
                    'Shipping Fee': shipping_cost,
                    'Position': rank + 1,
                    'ISBN': isbn,
                    'Seller Name': seller_name,
                }
        else:
            self.logger.info(f"Non-HTML response received from {response.url}")

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f'HTTP Error occurred: {response.status} on {response.url}')
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error(f'DNS Lookup Error occurred: {request.url}')
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error(f'Timeout Error occurred: {request.url}')
        elif failure.check(TunnelError):
            request = failure.request
            self.logger.error(f'Tunnel Error occurred: {request.url}')
        else:
            self.logger.error(f'Other Error occurred: {failure}')
