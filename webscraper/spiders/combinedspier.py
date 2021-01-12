# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
import json
from nested_lookup import nested_lookup


class combined(scrapy.Spider):
    name = 'combined'
    custom_settings = {'CONCURRENT_REQUESTS': 30,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'combined.csv',
                       'RETRY_TIMES': 5,
                       'COOKIES_ENABLED': False,
                       'FEED_EXPORT_ENCODING' : "utf-8"
    }

    proxy = 'http://xavigv:GOkNQBPK2DplRGqw@proxy.packetstream.io:31112'

    def __init__(self, cat=None, *args, **kwargs):
        super(combined, self).__init__(*args, **kwargs)
        self.cat = cat

    def start_requests(self):

        sheet = self.cat
        sheet = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRpzdf2pv1YKtA27XTP3A8RB0tevS0uuf0aCVpejqcU9-pACA7RM2j1zRCwjpPNOCQMrGCsZm1zf_pn/pub?output=csv'
        df = pd.read_csv(sheet)
        for i in range(len(df)):
            data = dict(df.iloc[i])
            url = data['URL']
            if 'tesco.com' in url:
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

                yield scrapy.Request(url, headers=headers, callback=self.parse_tesco, meta={"proxy": self.proxy},
                                     dont_filter=True)
            elif 'morrisons.com' in url:

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

                sku = url.split('-')[-1].strip()
                sku_url = f"https://groceries.morrisons.com/webshop/api/v1/products?skus={sku}"

                yield scrapy.Request(
                    url=sku_url,
                    headers=headers,
                    callback=self.parse_morrisons
                )
            elif 'ocado.com' in url:
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

                sku = url.split('-')[-1].strip()
                sku_url = f"https://www.ocado.com/webshop/api/v1/products?skus={sku}"

                yield scrapy.Request(
                    url=sku_url,
                    headers=headers,
                    callback=self.parse_ocado
                )
            elif 'sainsburys' in url:
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
                api_url = f"https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter[product_seo_url]=gb/groceries/{url.split('product/')[1]}&include[ASSOCIATIONS]=true&include[DIETARY_PROFILE]=true"
                yield scrapy.Request(api_url,
                             headers=headers,
                             callback=self.parse_sainsbury,
                             dont_filter=True,
                            meta= {
                                'url' : url
                            })
            elif 'britishcornershop' in url:
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
                yield scrapy.Request(url=url,
                                     headers=headers,
                                     callback=self.parse_britishcorner)

            elif 'britsuperstore.com' in url:
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

                yield scrapy.Request(url=url,
                                     headers=headers,
                                     callback=self.parse_britsuperstore)

    def parse_britsuperstore(self,response):

        sub_cat = ''.join(
            [i.strip() for i in response.xpath('//div[@class="breadcrumbs"]//li//text()').getall()]).replace('|', ' > ')
        cat = sub_cat.split('>')[-2]
        title_main = response.xpath('//div[@class="product-name"]//h1/text()').get('')
        price = response.xpath('//div[@class="product-shop"]//*[@class="price"]/text()').get('')
        img = response.xpath('//*[@class= "product-image"]//img/@src').get('')
        available = response.xpath('*//button[@title="Add to Cart"]')
        if available:
            availablility = 'Yes'
        else:
            availablility = 'No'
        item = {
            'Product Name': title_main,
            'Price ': price,
            'Price per quantity': '',
            'Image URL': img,
            'Image Path': 'images/' + title_main.replace('/', '_')  + '.' + img.split('.')[-1].split('?')[0],
            'Category': cat,
            'Subcategory': sub_cat,
            'Availability': availablility,
            'Product URL': response.url,
            'Review Count': '',
            'Weight': '',
            'Brand': '',
            'Store' : 'BritSuperstore'
        }
        yield item

    def parse_britishcorner(self,response):
        breadcrumbs = ' > '.join(
            [i.strip() for i in response.xpath('//*[@class="breadcrumbs content-container clear"]//li//text()').getall()
             if i.strip() and i.strip() != 'Home'])

        image_link = response.urljoin(response.xpath('//div[@class="product-image"]//img/@src').get(''))
        title_main = response.xpath('//h1/text()').get('')
        m_rrp = response.xpath('//div[@class="price clear"]//strong/text()').get('')

        available = response.xpath('//img[@alt="In Stock"]').get('')

        number_of_reviews = ' '.join(
            [i.strip() for i in response.xpath('//div[@class="ratings"]/parent::a/text()').getall() if
             i.strip()]).replace('Reviews', '').replace('Review', '').strip()

        if available:
            availablility = 'Yes'
        else:
            availablility = 'No'

        item = {
            'Product Name': title_main,
            'Price ': m_rrp,
            'Price per quantity': '',
            'Image URL': image_link,
            'Image Path': 'images/' + title_main.replace('/', '_') + '.' + image_link.split('.')[-1].split('?')[0],
            'Category': breadcrumbs.split('>')[-1].strip(),
            'Subcategory': breadcrumbs,
            'Availability': availablility,
            'Product URL': response.url,
            'Review Count': number_of_reviews,
            'Weight': response.xpath('//li[@class="weight"]/text()').get('').strip(),
            'Brand': response.xpath('//li[@class="brand"]/a/text()').get(''),
            'Store' : 'Britishcorner'
        }
        yield item
    def parse_sainsbury(self,response):

        json_dict = json.loads(response.text)
        name = json_dict['products'][0]['name']
        unit_price = json_dict['products'][0]['unit_price']
        retail_price = json_dict['products'][0]['retail_price'].get('price','')
        unit_price_string  = f"{unit_price.get('price','')} per {unit_price.get('measure_amount','')} {unit_price.get('measure','')}"
        sub_category = ' > '.join([i.get('label','') for i in json_dict['products'][0]['breadcrumbs']])
        category = sub_category.split('>')[-1]

        final_item = {
            'Product Name': name,
            'Price ': retail_price,
            'Price per quantity': unit_price_string,
            'Image URL': '',
            'Image Path': '',
            'Category': category,
            'Subcategory': sub_category,
            'Availability': '',
            'Product URL': response.meta['url'],
            'Review Count': '',
            'Weight': '',
            'Brand': '',
            'Store' : 'Sainsbury'
        }
        try:
            review_count = json_dict['products'][0]['reviews']['total']
        except:
            review_count = ''
        try:
            image = nested_lookup('url', json_dict['products'][0]['assets']['images'])[-1]
            final_item['Image URL'] = image
            final_item['Image Path'] = 'images/' + final_item['Product Name'].replace('/', '_') + '_' + json_dict['products'][0]['product_uid'] + '.' + image.split('.')[-1].split('?')[0]

        except:
            final_item['Image URL'] = ''
            final_item['Image Path'] = ''

        av = json_dict['products'][0]['is_available']
        if av:
            final_item['Availability'] = 'Yes'
        else:
            final_item['Availability'] = 'No'

        final_item['Review Count'] = review_count
        yield final_item
    def parse_ocado(self,response):
        items = json.loads(response.text)
        for item in items:
            sku = item.get('sku', '')
            url = f"https://www.ocado.com/products/{sku}"
            name = item.get('name', '')
            price_dict = item.get('price', {})
            price = price_dict.get('current', '')
            unit_price_dict = price_dict.get('unit', {})
            unit_price = f"{unit_price_dict.get('price', '')} {unit_price_dict.get('per', '')}"
            image_url = f"https://www.ocado.com/productImages/{sku[:3]}/{sku}_0_640x640.jpg"
            sub_category = item.get('mainCategory', '').replace('/', '>')
            weight = item.get('catchWeight', '')
            try:
                if 'OOS' in item['labels']:
                    availability = 'No'
                else:
                    availability = 'Yes'
            except:
                availability = 'Yes'

            review_count = item.get('reviewStats', {}).get('count', '')
            category = sub_category.split('>')[-1].strip()

            final_item = {
                'Product Name': name,
                'Price ': '£ ' + str(price),
                'Price per quantity': '£ ' + str(unit_price),
                'Image URL': image_url,
                'Image Path': 'images/' + name.replace('/', '_') + '_' + sku + '.' +
                              image_url.split('.')[-1].split('?')[0],
                'Category': category,
                'Subcategory': sub_category,
                'Availability': availability,
                'Product URL': url,
                'Review Count': review_count,
                'Weight': weight,
                'Brand': '',
                'Store' : 'Ocado'
            }
            yield final_item
    def parse_morrisons(self,response):
        items = json.loads(response.text)
        for item in items:
            sku = item.get('sku', '')
            url = f"https://groceries.morrisons.com/products/{sku}"
            name = item.get('name', '')
            price_dict = item.get('price', {})
            price = price_dict.get('current', '')
            unit_price_dict = price_dict.get('unit', {})
            unit_price = f"{unit_price_dict.get('price', '')} {unit_price_dict.get('per', '')}"
            image_url = f"https://groceries.morrisons.com/productImages/{sku[:3]}/{sku}_0_640x640.jpg"
            sub_category = item.get('mainCategory', '').replace('/', '>')
            weight = item.get('catchWeight', '')
            try:
                if 'OOS' in item['labels']:
                    availability = 'No'
                else:
                    availability = 'Yes'
            except:
                availability = 'Yes'

            review_count = item.get('reviewStats', {}).get('count', '')
            category = sub_category.split('>')[-1].strip()

            final_item = {
                'Product Name': name,
                'Price ': '£ ' + str(price),
                'Price per quantity': '£ ' + str(unit_price),
                'Image URL': image_url,
                'Image Path': 'images/' + name.replace('/', '_') + '_' + sku + '.' +
                              image_url.split('.')[-1].split('?')[0],
                'Category': category,
                'Subcategory': sub_category,
                'Availability': availability,
                'Product URL': url,
                'Review Count': review_count,
                'Weight': weight,
                'Brand': '',
                'Store':'Morrisons'
            }


            yield final_item
    def parse_tesco(self,response):
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
            'Image Path': 'images/' + title_main.replace('/', '_') + '.' + image_link.split('.')[-1].split('?')[0],
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
