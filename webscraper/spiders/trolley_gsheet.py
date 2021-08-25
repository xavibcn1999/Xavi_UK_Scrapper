# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
import json
from nested_lookup import nested_lookup
import requests
from scrapy.selector import Selector

from scrapy.utils.response import open_in_browser

class gsheet_trolley(scrapy.Spider):
    name = 'gsheet_trolley'
    custom_settings = {'CONCURRENT_REQUESTS': 1,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'gsheet_trolley.csv',
                       'RETRY_TIMES': 10,
                       'FEED_EXPORT_ENCODING' : "utf-8",
                       'COOKIES_ENABLED' : False

    }

    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'

    input_file = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQtb-UKr49Cj5tAof845aBQnN6Z_fnfaeGvvfKjee-XWz2OmNFlqW-XkItXUkhjEt7Xnr50yGdu_wcC/pub?output=csv'
    proxies = {"http": 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112',
               "https": 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'
               }

    #
    # def __init__(self, cat=None, *args, **kwargs):
    #     super(combined, self).__init__(*args, **kwargs)
    #     self.cat = cat

    def start_requests(self):

        df = pd.read_csv(self.settings.get('INPUT_FILE'))
        for i in range(len(df)):
        # for i in range(1):
            data = dict(df.iloc[i])
            url = data['URL']

            # url = 'https://trolley.co.uk/browse/baby-toddler-kids'

            if  'trolley.co.uk' in url:
                headers = {
                    'Connection': 'keep-alive',
                    'Cache-Control': 'max-age=0',
                    'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                    'sec-ch-ua-mobile': '?0',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7',
                }

                yield scrapy.Request(url, headers=headers, callback=self.parse_trolley, meta={"proxy": self.proxy},
                                     dont_filter=True)


    def parse_trolley(self,response):

        links = response.xpath('//div[@class="product-listing"]/a/@href').getall()

        for link in links:
            yield scrapy.Request(
                url = response.urljoin(link),
                callback=self.parse_detail,
                meta={
                    "proxy": self.proxy
                }
            )
            # break

        next_page = response.xpath('//a[@class="-next"]/@href').get('')

        if next_page:
            yield scrapy.Request(
                url = response.urljoin(next_page),
                callback=self.parse_trolley,
                meta={
                    "proxy": self.proxy
                }
            )


    def parse_detail(self,response):

        brand = response.xpath('//span[@class="_brand"]//text()').get('')
        name = response.xpath('//span[@class="_name"]//text()').get('')

        if not name:

            name = ' '.join([i.strip() for i in response.xpath('//h1[@class="product-header"]/text()').getall() if i.strip()])

        quantity = response.xpath('//span[@class="_item -qty"]//text()').get('')
        weights = response.xpath('//span[@class="_item -size"]//text()').get('')



        image = response.xpath('//div[@class="product-img -large"]//img/@src').get('')
        if image:
            image_url = response.urljoin(image)
            image_path = image.split('/')[-1] + '.jpeg'
        else:
            image_url = ''
            image_path = ''

        markets = response.xpath('//div[@class="comparison-table"]/div')

        item = {
            'Brand' : brand,
            'Product Name' : name,
            'Units' : quantity,
            'Weight' : weights,
            'Image URLe' : f"images/{image_path}",
            'Image URL' : image_url,
            'URL' : response.url
        }

        for market in markets:
            store_name = market.xpath('.//svg[contains(@class,"store-logo")]/@title').get('')
            price = market.xpath('.//div[@class="_price"]//text()').get('')

            store_url = market.xpath('.//a[@class="cta"]/@href').get('').split('=')[1].replace('%3A%2F%2F','://').replace('%2F','/')

            final_item = {
                **item,
                'Stores' : store_name,
                'Price' : price,
                'Store URLs' : store_url
            }

            yield final_item




