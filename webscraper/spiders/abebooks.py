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



class abebooks(scrapy.Spider):
    name = 'abebooks'
    custom_settings = {'CONCURRENT_REQUESTS': 1,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'abebooks.csv',
                       'RETRY_TIMES': 15,
                       'COOKIES_ENABLED': False,
                       'FEED_EXPORT_ENCODING' : "utf-8"
    }
    headers = {
        'authority': 'www.abebooks.co.uk',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }


    proxy = 'http://xavigv:GOkNQBPK2DplRGqw_country-UnitedKingdom@proxy.packetstream.io:31112'

    def __init__(self, url=None, *args, **kwargs):
        super(abebooks, self).__init__(*args, **kwargs)
        self.url = url

   
    # file = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'
    # url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'
    
    # url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRtbluXDoMi--POZYgVYruqgotcT7PT2mbVi4Ic2Rf87ycyQ6b1gmzdT_1I41IHoHPqVsM_2V-nAic4/pub?gid=0&single=true&output=csv'
    def start_requests(self):

        df = pd.read_csv(self.url)

        url_list = [i for i in df['url'].tolist() if i.strip()]

        for request_url in url_list:
            yield scrapy.Request(url=request_url, callback=self.parse, headers=self.headers, meta={'proxy': self.proxy})
       

    def parse(self, response):
        listings = response.xpath('//li[@data-cy="listing-item"]')[:3]

        for rank, listing in enumerate(listings):

            title = listing.xpath('.//span[@data-cy="listing-title"]/text()').get('')

            price = listing.xpath('.//meta[@itemprop="price"]/@content').get('')

            isbn = listing.xpath('.//meta[@itemprop="isbn"]/@content').get('')

            seller_name = listing.xpath('.//a[@data-cy="listing-seller-link"]/text()').get('')

            shipping_cost = listing.xpath('.//span[contains(@id,"item-shipping-price-")]/text()').get('')

            image = listing.xpath('.//div[@data-cy="listing-image"]/img/@src').get('')
            
            yield {
                'URL': response.url,
                'Image URL': image,
                'Product Title': title,
                'Product Price': price,
                'Shipping Fee': shipping_cost,
                'Postion': rank + 1,
                'ISBN': isbn,
                'Seller Name': seller_name,


            }





      





        

        
       
