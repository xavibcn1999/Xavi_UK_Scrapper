# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
import json
from nested_lookup import nested_lookup
import requests
from scrapy.selector import Selector

class google_sheet_tesco(scrapy.Spider):
    name = 'google_sheet_tesco'
    custom_settings = {'CONCURRENT_REQUESTS': 5,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'google_sheet_tesco.csv',
                       'RETRY_TIMES': 10,
                       'FEED_EXPORT_ENCODING' : "utf-8",
                       'COOKIES_ENABLED' : False

    }

    # proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'
    proxy = 'http://amitupreti:RefzyvyXp1QVZRfx@proxy.packetstream.io:31112'

    input_file = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQtb-UKr49Cj5tAof845aBQnN6Z_fnfaeGvvfKjee-XWz2OmNFlqW-XkItXUkhjEt7Xnr50yGdu_wcC/pub?output=csv'
    proxies = {"http": 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112',
               "https": 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'
               }

    #
    # def __init__(self, cat=None, *args, **kwargs):
    #     super(combined, self).__init__(*args, **kwargs)
    #     self.cat = cat

    def start_requests(self):

        sheet = self.input_file
        df = pd.read_csv(sheet)
        for i in range(len(df)):
            data = dict(df.iloc[i])
            url = data['URL']
            if  'tesco.com' in url:
                headers = {
                    'authority': 'www.tesco.com',
                    'cache-control': 'max-age=0',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'sec-fetch-site': 'none',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-user': '?1',
                    'sec-fetch-dest': 'document',
                    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7'
                }

                yield scrapy.Request(url, headers=headers, callback=self.parse_tesco, cookies= {}, meta={"proxy": self.proxy},
                                     dont_filter=True)


    def parse_tesco(self,response):
        products = response.xpath('//*[@data-auto="product-list"]//div[@class="tile-content"]/a/@href').getall()
        heading = response.xpath('//h1[@class="heading query"]//text()').get('')

        for product in products:
            yield scrapy.Request(url=response.urljoin(product),
                                 callback=self.parse_tesco_items,
                                 dont_filter=True,
                                 cookies= {},
                                 meta={"proxy": self.proxy,
                                       "heading": heading})

        next_page = response.xpath('//*[@class="icon-icon_whitechevronright"]/parent::a/@href').get('')
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page),
                                 callback=self.parse_tesco,
                                 cookies={},
                                 meta={"proxy": self.proxy})
    def parse_tesco_items(self,response):
        breadcrumbs = ' > '.join(response.xpath('//nav[@aria-label="breadcrumb"]//li//text()').getall())
        image_link = response.xpath('//div[@class="product-image__container"]/img/@src').get('')
        title_main = response.xpath('//h1/text()').get('')
        try:
            price_control = response.xpath('//div[@class="price-details--wrapper"]')[0]
            m_rrp = ''.join(price_control.xpath('.//div[@class="price-control-wrapper"]//text()').getall())
            m_ppq = ''.join(price_control.xpath('.//div[@class="price-per-quantity-weight"]//text()').getall())
        except:
            m_rrp = ''
            m_ppq = ''

        available = response.xpath(
            '//div[@class="product-details-tile"]//span[@aria-hidden="true"][contains(text(),"Add")]').get('')
        try:
            number_of_reviews = response.xpath('//div[@id="review-data"]//h4/text()').get('').replace('Reviews',
                                                                                                      '').replace(
                'Review', '').strip()
        except:
            number_of_reviews = 0
        if available:
            availablility = 'Yes'
        else:
            availablility = 'No'

        item = {
            'Product Name': title_main,
            'Price ': m_rrp,
            'Price per quantity': m_ppq,
            'Image URL': image_link,
            'Image Path': 'gsheet_images/tesco_' + title_main.replace('/', '_') + '.' + image_link.split('.')[-1].split('?')[0],
            'Category': breadcrumbs.split('>')[-1].strip(),
            'Subcategory': breadcrumbs,
            'Availability': availablility,
            'Product URL': response.url,
            'Review Count': number_of_reviews,
            'Weight': '',
            'Brand': '',
            'Store' : 'Tesco'
        }
        yield item
