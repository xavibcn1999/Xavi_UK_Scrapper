# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
from fake_headers import Headers

from scrapy.utils.response import open_in_browser
#import open_in_browser(response)
header = Headers(browser="chrome",  # Generate only Chrome UA
                 os="win",  # Generate ony Windows platform
                 headers=True)



class wob(scrapy.Spider):
    name = 'wob'
    custom_settings = {'CONCURRENT_REQUESTS': 1,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'ebay.csv',
                       'RETRY_TIMES': 15,
                       'COOKIES_ENABLED': False,
                       'FEED_EXPORT_ENCODING' : "utf-8"
    }
    headers = {
        'authority': 'www.ebay.com',
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

    proxy = 'http://xavigv:GOkNQBPK2DplRGqw_country-UnitedKingdom@proxy.packetstream.io:31112'

    # def __init__(self, url=None, *args, **kwargs):
    #     super(wob, self).__init__(*args, **kwargs)
    #     self.url = url

   
    # file = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'
    # url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'
    
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ_8YsQ7wbLePLwLuVuz8bBM9yXqD_ft6eyubLVMJ1At6mGtnXqjD3BIEhpa5QnyrAE5wC7skw1z4Ng/pub?gid=0&single=true&output=csv'
    def start_requests(self):

        df = pd.read_csv(self.url)

        url_list = [i for i in df['url'].tolist() if i.strip()]

        for request_url in url_list:
          
            yield scrapy.Request(url=request_url, callback=self.parse, headers=self.headers, 
            meta={'proxy': self.proxy})
       

    def parse(self, response):

        title = ' '.join([i.strip() for i in response.xpath('//h1[@class="title d-none d-md-block"]//text()').getall() if i.strip()])

        price = response.xpath('//div[@class="price"]/text()').get('').strip()

        image = response.xpath('//div[@class="imageHolder"]//img/@src').get('')

        
        conditon = response.xpath('//div[@class="condition"]/span/text()').get('')

        isbn_13 = response.xpath('//label[@class="attributeTitle" and contains(text(),"ISBN 13")]/following-sibling::div/text()').get('')
        isbn_10 = response.xpath('//label[@class="attributeTitle" and contains(text(),"ISBN 10")]/following-sibling::div/text()').get('')
       

        item = {
            'URL': response.url,
            'Image URL': image,
            'Product Title': title,
            'Product Price': price,
            'Condition': conditon,
            'ISBN 13': isbn_13,
            'ISBN 10': isbn_10,


        }
       
        yield item