# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
from fake_headers import Headers
from scrapy.utils.response import open_in_browser

header = Headers(browser="chrome",  # Generate only Chrome UA
                 os="win",  # Generate ony Windows platform
                 headers=True)

class aa_wob(scrapy.Spider):
    name = 'aa_wob'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'wob.csv',
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': False,
        'FEED_EXPORT_ENCODING': "utf-8"
    }
    headers = {
        'authority': 'www.wob.com',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
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
        super(aa_wob, self).__init__(*args, **kwargs)
        self.url = url

    def start_requests(self):
        df = pd.read_csv(self.url)
        url_list = [i for i in df['url'].tolist() if i.strip()]

        for request_url in url_list:
            yield scrapy.Request(url=request_url, callback=self.parse, headers=self.headers, meta={'request_url': request_url})

    def parse(self, response):
        title = ' '.join([i.strip() for i in response.xpath('//h1[@class="title d-none d-md-block"]//text()').getall() if i.strip()])
        image = response.xpath('//div[@class="imageHolder"]//img/@src').get('')
        isbn_13 = response.xpath('//label[@class="attributeTitle" and contains(text(),"ISBN 13")]/following-sibling::div/text()').get('')
        if isbn_13:
            isbn_13 = f"'{isbn_13.strip()}"  # Asegurarse de que el ISBN sea tratado como cadena de texto

        # Extraer el precio y el estado principal de arriba
        main_price = response.xpath('//div[@class="order-md-1 prices mt-md-3"]//div[@class="price"]/text()').get('').strip()
        main_condition = response.xpath('//div[@class="order-md-1 prices mt-md-3"]//div[@class="condition"]/span/text()').get('')

        # Crear un item para el precio y estado principal si tiene precio
        if main_price:
            main_item = {
                'URL': response.url,
                'Image URL': image,
                'Product Title': title,
                'Product Price': main_price,
                'Condition': main_condition,
                'ISBN 13': isbn_13,
            }
            yield main_item

        # Extraer variantes si existen y tienen precio
        variants = response.xpath('//div[@class="variants order-md-2"]/a')
        for variant in variants:
            condition = variant.xpath('.//span[@class="variantName"]/text()').get('')
            price = variant.xpath('.//span[@class="variantPrice"]/text()').get('').strip()
            if price:
                item = {
                    'URL': response.url,
                    'Image URL': image,
                    'Product Title': title,
                    'Product Price': price,
                    'Condition': condition,
                    'ISBN 13': isbn_13,
                }
                yield item
