# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import json

#from scrapy.utils.response import open_in_browser
#open_in_browser(response)


class sainsbury(scrapy.Spider):
    name = 'sainsbury'
    custom_settings = {'CONCURRENT_REQUESTS': 30,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'sainsbury.csv',
                       'RETRY_TIMES': 5,
                       'COOKIES_ENABLED': True,
                       'FEED_EXPORT_ENCODING' : "utf-8",

    }
    headers = {
        'authority': 'www.sainsburys.co.uk',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7',
    }
    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'

    # def __init__(self, cat=None, *args, **kwargs):
    #     super(tesco3, self).__init__(*args, **kwargs)
    #     self.cat = cat

    def start_requests(self):

        url = "https://www.sainsburys.co.uk/webapp/wcs/stores/servlet/gb/groceries/bakery/all-bread"
        yield scrapy.Request(url,
                             headers=self.headers,
                             callback=self.parse,
                             meta={"proxy": self.proxy},
                             dont_filter=True)

    def parse(self, response):
        products = response.xpath('//div[@class="productInfo"]')
        for product in products:
            name = product.xpath('.//h3/a/text()').get('').strip()
            url = product.xpath('.//h3/a/@href').get('')
            trolly = product.xpath('./following-sibling::div[@class="addToTrolleytabBox"]')[0]
            price = trolly.xpath('.//*[@class="pricePerUnit"]/text()').get('').strip()
            ppq = ' '.join(trolly.xpath('.//*[@class="pricePerMeasure"]//text()').getall()).strip()
            sku_id = trolly.xpath('.//input[@name="ItemSKU_ID"]/@value').get('')
            image = f"https://assets.sainsburys-groceries.co.uk/gol/{sku_id}/1/300x300.jpg"
            add  = trolly.xpath('.//*[@class="button process addQty  "]').get('')
            if add:
                available = 'Yes'
            else:
                available = 'No'
            navs = response.xpath('//ul[@id="breadcrumbNavList"]//li[@class]/a//text()').getall()
            category = navs[-1]
            sub_category = ' > '.join(navs)
            try:
                reviews = ''.join([i.strip() for i in trolly.xpath('.//*[@class="numberOfReviews"]//text()').getall()]).split('(')[1].split(')')[0]
            except:
                reviews = ''

            final_item = {
                'Product Name': name,
                'Price ': price,
                'Price per quantity': ppq,
                'Image URL': image,
                'Image Path': 'images/' + name.replace('/', '_') + '_' + sku_id + '.' +
                              image.split('.')[-1].split('?')[0],
                'Category': category,
                'Subcategory': sub_category,
                'Availability': available,
                'Product URL': url,
                'Review Count': reviews,
                'Weight': ''
            }

            if trolly.xpath('.//div[@class="reviews"]').get(''):
                yield final_item

            else:
                url  = f"https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter[product_seo_url]={url.split('shop/')[1]}&include[ASSOCIATIONS]=true&include[DIETARY_PROFILE]=true"
                yield scrapy.Request(
                    url = url,
                    callback=self.parse_details,
                    headers=self.headers,
                    meta={"proxy": self.proxy, "final_item" : final_item}
                )
        next_page = response.xpath('//li[@class="next"]/a/@href').get('')
        if next_page:
            yield scrapy.Request(url = next_page,
                                 headers=self.headers,
                                 callback=self.parse,
                                 meta={"proxy": self.proxy})


    def parse_details(self,response):
        final_item = response.meta['final_item']
        json_dict = json.loads(response.text)
        try:
            review_count = json_dict['products'][0]['reviews']['total']
        except:
            review_count = ''
        final_item['Review Count'] = review_count
        yield final_item







