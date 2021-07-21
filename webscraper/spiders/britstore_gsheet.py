# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd


class gsheet_britsuperstore(scrapy.Spider):
    name = 'gsheet_britsuperstore'
    custom_settings = {'CONCURRENT_REQUESTS': 5,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'gsheet_britsuperstore.csv',
                       'RETRY_TIMES': 20,
                       'COOKIES_ENABLED': False,
                       'FEED_EXPORT_ENCODING' : "utf-8"
    }
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7',
    }
    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'



    def start_requests(self):

        df = pd.read_csv(self.settings.get('INPUT_FILE'))
        for i in range(len(df)):
            data = dict(df.iloc[i])
            url = data['URL']
            if 'britsuperstore' not in url:
                continue

            yield scrapy.Request(url, headers=self.headers, callback=self.parse, meta={"proxy": self.proxy},
                                 dont_filter=True)

    def parse(self, response):
        rows = response.xpath('//*[@class="products-list"]/li')

        cat = response.xpath('//h1/text()').get('')
        sub_cat = ''.join([i.strip() for i in response.xpath('//div[@class="breadcrumbs"]//li//text()').getall()]).replace('|', ' > ')

        for row in rows:
            pid = row.xpath('./@id').get('').split('-')[-1]
            title_main = ' '.join([i.strip() for i in row.xpath('.//h2[@class="product-name"]//text()').getall()]).strip()
            price = row.xpath('.//*[@class= "price"]/text()').get('')
            img = row.xpath('.//*[@class= "product-image"]//a[@title="View Details"]//img/@src').get('')
            available =  row.xpath('.//button[@title="Add to basket"]')
            if available:
                availablility = 'Yes'
            else:
                availablility = 'No'
            item = {
                'Product Name': title_main,
                'Price ': price,
                'Price per quantity': '',
                'Image URL': img,
                'Image Path': 'images/' + img.split('/')[-1].split('?')[0],
                'Category': cat,
                'Subcategory': sub_cat,
                'Availability': availablility,
                'Product URL': row.xpath('.//a[@title="View Details"]/@href').get(''),
                'Review Count': '',
                'Weight': '',
                'Brand': '',
                'Store': 'BritSuperstore'
            }

            yield item
        next_page =  response.xpath('//a[@title="Next"]/@href').get('')

        if next_page:
            yield scrapy.Request(url = response.urljoin(next_page),
                                 headers=self.headers,
                                 callback=self.parse,
                                 meta={"proxy": self.proxy})
