# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd

#from scrapy.utils.response import open_in_browser
#import open_in_browser(response)



class gsheet_britishcorner(scrapy.Spider):
    name = 'gsheet_britishcorner'
    custom_settings = {'CONCURRENT_REQUESTS': 30,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'gsheet_britishcorner.csv',
                       'RETRY_TIMES': 5,
                       'COOKIES_ENABLED': True,
                       'FEED_EXPORT_ENCODING' : "utf-8"
    }
    headers = {
        'authority': 'www.britishcornershop.co.uk',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'sec-ch-ua-mobile': '?0',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.britishcornershop.co.uk/cakes-and-cake-bars-bakery',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7',
    }

    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'



    def start_requests(self):
        url = 'https://www.britishcornershop.co.uk'
        yield scrapy.Request(url, headers=self.headers, callback=self.start_requests1, meta={"proxy": self.proxy},
                             dont_filter=True)

    def start_requests1(self,response):
        url = 'https://www.britishcornershop.co.uk/shopping_basket.asp?action=country&cid=0'
        yield scrapy.Request(url, callback=self.start_requests2, meta={"proxy": self.proxy},
                             dont_filter=True)

    def start_requests2(self,response):

        df = pd.read_csv(self.settings.get('INPUT_FILE'))
        for i in range(len(df)):
            data = dict(df.iloc[i])
            url = data['URL']
            try:
                country = data['country']
            except:
                country = ''
            if not country:
                country = '788'
            else:
                country = str(country)
            if 'britishcornershop' not in url:
                continue


            token = response.xpath('//input[@name="token"]/@value').get('')
            data = {
                'token': token,
                'countryid': country
            }
            yield scrapy.FormRequest(

                url= 'https://www.britishcornershop.co.uk/shopping_basket.asp?action=country',
                formdata=data,
                callback=self.start_requests3,
                meta= {
                    'cat_url' : url
                },
                dont_filter=True
            )

    def start_requests3(self,response):

        url = response.meta['cat_url']
        yield scrapy.Request(url, headers=self.headers, callback=self.parse, meta={"proxy": self.proxy},
                             dont_filter=True)

    def parse(self, response):
        products = response.xpath('//div[@class="product-details"]')
        heading = response.xpath('//h1/text()').get('')
        breadcrumbs = ' > '.join([i.strip() for i in response.xpath('//*[@class="breadcrumbs content-container clear"]//li//text()').getall() if i.strip() and i.strip()!='Home'])

        for product in products:
            link = product.xpath('.//a/@href').get('')
            yield scrapy.Request(url = response.urljoin(link),
                                 headers=self.headers,
                                 callback=self.parse_details,
                                 meta={"proxy": self.proxy,
                                       "heading": heading,
                                       "subcat" : breadcrumbs})


        next_page = response.urljoin(response.xpath('//li/a[contains(text(),"Next")]/@href').get(''))
        if next_page and 'javascript' not in next_page:
            yield scrapy.Request(url = next_page,
                                 headers=self.headers,
                                 callback=self.parse,
                                 meta={"proxy": self.proxy})




    def parse_details(self, response):
        breadcrumbs = response.meta['subcat']
        image_link = response.urljoin(response.xpath('//div[@class="product-image"]//img/@src').get(''))
        title_main = response.xpath('//h1/text()').get('')
        m_rrp = response.xpath('//div[@class="price clear"]//strong/text()').get('')

        available = response.xpath('//img[@alt="In Stock"]').get('')

        number_of_reviews = ' '.join([i.strip() for i in response.xpath('//div[@class="ratings"]/parent::a/text()').getall() if i.strip()]).replace('Reviews','').replace('Review','').strip()

        if available:
            availablility = 'Yes'
        else:
            availablility = 'No'

        item = {
            'Product Name': title_main,
            'Price ': m_rrp,
            'Price per quantity': '',
            'Image URL': image_link,
            'Image Path' : 'Britishcorner/'+title_main.replace('/','_')+'.'+image_link.split('.')[-1].split('?')[0],
            'Category' : breadcrumbs.split('>')[-1].strip(),
            'Subcategory': breadcrumbs,
            'Availability' : availablility,
            'Product URL': response.url,
            'Review Count': number_of_reviews,
            'Weight':  response.xpath('//li[@class="weight"]/text()').get('').strip(),
            'Brand' : response.xpath('//li[@class="brand"]/a/text()').get(''),
            'Store' : 'Britishcorner'
        }
        yield item
