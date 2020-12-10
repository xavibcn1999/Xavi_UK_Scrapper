# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import xmltodict
import shutil
import os
import json
from nested_lookup import nested_lookup
from pathlib import Path
import requests
import argparse


class tesco3(scrapy.Spider):
    name = 'tesco3'
    custom_settings = {'CONCURRENT_REQUESTS': 3,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'tesco3.csv',
                       'RETRY_TIMES': 5,
                       'COOKIES_ENABLED': False,
                       'CLOSESPIDER_ITEMCOUNT' : 100

                       }
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
    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'

    def start_requests(self):

        url = 'https://www.tesco.com/groceries/en-GB/shop/christmas/all'
        yield scrapy.Request(url, headers=self.headers, callback=self.parse, meta={"proxy": self.proxy},
                             dont_filter=True)

    def parse(self, response):
        products = response.xpath('//*[@data-auto="product-list"]//div[@class="tile-content"]/a/@href').getall()
        heading = response.xpath('//h1[@class="heading query"]//text()').get('')

        for product in products:
            yield scrapy.Request(url = response.urljoin(product),
                                 headers=self.headers,
                                 callback=self.parse_details,
                                 meta={"proxy": self.proxy,
                                       "heading": heading})

        next_page = response.xpath('//*[@class="icon-icon_whitechevronright"]/parent::a/@href').get('')
        if next_page:
            yield scrapy.Request(url = response.urljoin(next_page),
                                 headers=self.headers,
                                 callback=self.parse,
                                 meta={"proxy": self.proxy})




    def parse_details(self, response):
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

        available = response.xpath('//div[@class="product-details-tile"]//span[@aria-hidden="true"][contains(text(),"Add")]').get('')

        if available:
            availablility = 'Yes'
        else:
            availablility = 'No'

        item = {
            'Product Name': title_main,
            'Price ': m_rrp,
            'Price per quantity': m_ppq,
            'Image URL': image_link,
            'Category' : response.meta['heading'],
            'Subcategory': breadcrumbs,
            'Availability' : availablility,
            'Product URL': response.url

        }

        yield item
