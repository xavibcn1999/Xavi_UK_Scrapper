# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import requests
from scrapy.selector import Selector
from nested_lookup import nested_lookup
import json
class ocado(scrapy.Spider):
    name = 'ocado'
    custom_settings = {'CONCURRENT_REQUESTS': 30,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'ocado.csv',
                       'RETRY_TIMES': 5,
                       'COOKIES_ENABLED': False,
                       'FEED_EXPORT_ENCODING' : "utf-8",

    }
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7',


    }


    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'

    proxies = {"http": 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112',
               "https": 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'
               }

    def __init__(self, cat=None, *args, **kwargs):
        super(ocado, self).__init__(*args, **kwargs)
        self.cat = cat

    def start_requests(self):
        headers = {
            'Connection': 'keep-alive',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7'
        }
        url = self.cat
        success = False
        retry_times = 10
        while not success and retry_times >= 0:
            try:
                response = requests.get(url, proxies=self.proxies)
                if response.status_code == 200:
                    success = True
                    break
                else:
                    retry_times = retry_times - 1
            except Exception as e:
                print(e)
                retry_times = retry_times - 1

        resp = Selector(text=response.text)
        category = resp.xpath('//nav//li//text()').getall()[-1]
        json_dict = json.loads(resp.xpath('//script').get('').split('window.INITIAL_STATE = ')[1].rsplit(';', 1)[0])
        skus = list(set(nested_lookup('sku',json_dict)))
        skus_list = []

        for i in range(0,len(skus),6):
            small_list = skus[i:i+6]
            skus_list.append(small_list)


        for sku_l in skus_list:
            sku_string = ','.join(sku_l)
            sku_url = f"https://www.ocado.com/webshop/api/v1/products?skus={sku_string}"
            yield scrapy.Request(
                url = sku_url,
                headers = headers,
                callback= self.parse,
                meta = {'category' : category,'proxy':self.proxy}
            )



    def parse(self, response):
        items = json.loads(response.text)
        for item in items:
            sku = item.get('sku','')
            url = f"https://www.ocado.com/products/{sku}"
            name = item.get('name','')
            price_dict = item.get('price',{})
            price = price_dict.get('current','')
            unit_price_dict = price_dict.get('unit',{})
            unit_price = f"{unit_price_dict.get('price','')} {unit_price_dict.get('per','')}"
            image_url  = f"https://www.ocado.com/productImages/{sku[:3]}/{sku}_0_640x640.jpg"
            sub_category = item.get('mainCategory','').replace('/','>')
            weight = item.get('catchWeight','')
            try:
                if 'OOS' in item['labels']:
                    availability = 'No'
                else:
                    availability = 'Yes'
            except:
                availability = 'Yes'

            review_count = item.get('reviewStats',{}).get('count','')
            category = response.meta['category']

            final_item = {
                'Product Name' : name,
                'Price ' : '£ ' + str(price),
                'Price per quantity': '£ ' + str(unit_price),
                'Image URL': image_url,
                'Image Path': 'images/' + name.replace('/', '_') + '_'+ sku+ '.' + image_url.split('.')[-1].split('?')[0],
                'Category': category,
                'Subcategory': sub_category,
                'Availability': availability,
                'Product URL': url,
                'Review Count' : review_count,
                'Weight' : weight,
                'Brand': ''
            }


            yield final_item
