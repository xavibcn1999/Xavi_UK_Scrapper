# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
import json
from nested_lookup import nested_lookup
import requests
from scrapy.selector import Selector

class google_sheet(scrapy.Spider):
    name = 'google_sheet'
    custom_settings = {'CONCURRENT_REQUESTS': 5,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'google_sheet.csv',
                       'RETRY_TIMES': 5,
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

        sheet = self.input_file
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

                success = False
                retry_times = 10
                while not success and retry_times >= 0:
                    try:
                        response = requests.get(url)
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
                json_dict = json.loads(
                    resp.xpath('//script').get('').split('window.INITIAL_STATE = ')[1].rsplit(';', 1)[0])
                skus = list(set(nested_lookup('sku', json_dict)))

                data_sku = resp.xpath('//*[@data-sku]/@data-sku').getall()
                all_sku = list(set(skus + data_sku))
                skus_list = []

                for i in range(0, len(all_sku), 6):
                    small_list = skus[i:i + 6]
                    skus_list.append(small_list)

                for sku_l in skus_list:
                    sku_string = ','.join(sku_l)
                    sku_url = f"https://groceries.morrisons.com/webshop/api/v1/products?skus={sku_string}"
                    yield scrapy.Request(
                        url=sku_url,
                        headers=headers,
                        callback=self.parse_morrisons,
                        meta={'category': category, 'proxy': self.proxy}
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
                json_dict = json.loads(
                    resp.xpath('//script').get('').split('window.INITIAL_STATE = ')[1].rsplit(';', 1)[0])
                skus = list(set(nested_lookup('sku', json_dict)))
                skus_list = []

                for i in range(0, len(skus), 6):
                    small_list = skus[i:i + 6]
                    skus_list.append(small_list)

                for sku_l in skus_list:
                    sku_string = ','.join(sku_l)
                    sku_url = f"https://www.ocado.com/webshop/api/v1/products?skus={sku_string}"
                    yield scrapy.Request(
                        url=sku_url,
                        headers=headers,
                        callback=self.parse_ocado,
                        meta={'category': category, 'proxy': self.proxy}
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
                yield scrapy.Request(url,
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
                yield scrapy.Request(url='https://www.britishcornershop.co.uk',
                                     headers=headers,
                                     meta={
                                         'url': url
                                     },
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
                                     dont_filter=True,

                                     callback=self.parse_britsuperstore)

    def parse_britsuperstore(self,response):

        rows = response.xpath('//*[@class="products-list"]/li')

        cat = response.xpath('//h1/text()').get('')
        sub_cat = ''.join(
            [i.strip() for i in response.xpath('//div[@class="breadcrumbs"]//li//text()').getall()]).replace('|', ' > ')

        for row in rows:
            pid = row.xpath('./@id').get('').split('-')[-1]
            title_main = ' '.join(
                [i.strip() for i in row.xpath('.//h2[@class="product-name"]//text()').getall()]).strip()
            price = row.xpath('.//*[@class= "price"]/text()').get('')
            img = row.xpath('.//*[@class= "product-image"]//a[@title="View Details"]//img/@src').get('')
            available = row.xpath('.//button[@title="Add to basket"]')
            if available:
                availablility = 'Yes'
            else:
                availablility = 'No'
            item = {
                'Product Name': title_main,
                'Price ': price,
                'Price per quantity': '',
                'Image URL': img,
                'Image Path': 'gsheet_images/BritSuperstore_' + title_main.replace('/', '_') + '.' + img.split('.')[-1].split('?')[0],
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
        next_page = response.xpath('//a[@title="Next"]/@href').get('')

        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page),
                                 callback=self.parse_britsuperstore,
                                 meta={"proxy": self.proxy})

    def parse_britishcorner(self,response):

        url = 'https://www.britishcornershop.co.uk/shopping_basket.asp?action=country&cid=0'
        yield scrapy.Request(url, callback=self.start_requests2, meta={"proxy": self.proxy,'url' : response.meta['url']},
                             dont_filter=True)

    def start_requests2(self, response):

        token = response.xpath('//input[@name="token"]/@value').get('')
        data = {
            'token': token,
            'countryid': '788'
        }
        yield scrapy.FormRequest(

            url='https://www.britishcornershop.co.uk/shopping_basket.asp?action=country',
            formdata=data,
            meta={"proxy": self.proxy, 'url': response.meta['url']},
            callback=self.start_requests3
        )

    def start_requests3(self, response):

        url = response.meta['url']
        yield scrapy.Request(url,callback=self.parse_britishcorner_1, meta={"proxy": self.proxy},
                             dont_filter=True)

    def parse_britishcorner_1(self, response):
        products = response.xpath('//div[@class="product-details"]')
        heading = response.xpath('//h1/text()').get('')
        breadcrumbs = ' > '.join(
            [i.strip() for i in response.xpath('//*[@class="breadcrumbs content-container clear"]//li//text()').getall()
             if i.strip() and i.strip() != 'Home'])

        for product in products:
            link = product.xpath('.//a/@href').get('')
            yield scrapy.Request(url=response.urljoin(link),
                                 callback=self.parse_britishcorner_2,
                                 meta={"proxy": self.proxy,
                                       "heading": heading,
                                       "subcat": breadcrumbs})

        next_page = response.urljoin(response.xpath('//li/a[contains(text(),"Next")]/@href').get(''))
        if next_page and 'javascript' not in next_page:
            yield scrapy.Request(url=next_page,
                                 callback=self.parse_britishcorner_1,
                                 meta={"proxy": self.proxy})

    def parse_britishcorner_2(self, response):
        breadcrumbs = response.meta['subcat']
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
            'Image Path': 'gsheet_images/Britishcorner_' + title_main.replace('/', '_') + '.' + image_link.split('.')[-1].split('?')[
                0],
            'Category': breadcrumbs.split('>')[-1].strip(),
            'Subcategory': breadcrumbs,
            'Availability': availablility,
            'Product URL': response.url,
            'Review Count': number_of_reviews,
            'Weight': response.xpath('//li[@class="weight"]/text()').get('').strip(),
            'Brand': response.xpath('//li[@class="brand"]/a/text()').get(''),
            'Store': 'Britishcorner'
        }
        yield item

    def parse_sainsbury(self,response):
        products = response.xpath('//div[@class="productInfo"]')
        for product in products:
            name = product.xpath('.//h3/a/text()').get('').strip()
            url = product.xpath('.//h3/a/@href').get('')
            trolly = product.xpath('./following-sibling::div[@class="addToTrolleytabBox"]')[0]
            price = trolly.xpath('.//*[@class="pricePerUnit"]/text()').get('').strip()
            ppq = ' '.join(trolly.xpath('.//*[@class="pricePerMeasure"]//text()').getall()).strip()
            sku_id = trolly.xpath('.//input[@name="ItemSKU_ID"]/@value').get('')

            navs = response.xpath('//ul[@id="breadcrumbNavList"]//li[@class]/a//text()').getall()
            category = navs[-1]
            sub_category = ' > '.join(navs)

            final_item = {
                'Product Name': name,
                'Price ': price,
                'Price per quantity': ppq,
                'Image URL': '',
                'Image Path': '',
                'Category': category,
                'Subcategory': sub_category,
                'Availability': '',
                'Product URL': url,
                'Review Count': '',
                'Weight': '',
                'Brand': '',
                'Store': 'Sainsbury'
            }
            api_url = f"https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter[product_seo_url]={url.split('shop/')[1]}&include[ASSOCIATIONS]=true&include[DIETARY_PROFILE]=true"
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_sainsbury_items,
                meta={"proxy": self.proxy, "final_item": final_item, "sku_id": sku_id,"url" :url}
            )
        next_page = response.xpath('//li[@class="next"]/a/@href').get('')

        if next_page:
            yield scrapy.Request(url=next_page,
                                 callback=self.parse_sainsbury,
                                 meta={"proxy": self.proxy})

    def parse_sainsbury_items(self,response):

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
            final_item['Image Path'] = 'gsheet_images/sainsbury_' + final_item['Product Name'].replace('/', '_') + '.' + image.split('.')[-1].split('?')[0]

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
                'Image Path': 'gsheet_images/ocado_' + name.replace('/', '_') +  '.' +
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
                'Image Path': 'gsheet_images/morrisons_' + name.replace('/', '_') +  '.' +
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
        products = response.xpath('//*[@data-auto="product-list"]//div[@class="tile-content"]/a/@href').getall()
        heading = response.xpath('//h1[@class="heading query"]//text()').get('')

        for product in products:
            yield scrapy.Request(url=response.urljoin(product),
                                 callback=self.parse_tesco_items,
                                 dont_filter=True,
                                 meta={"proxy": self.proxy,
                                       "heading": heading})

        next_page = response.xpath('//*[@class="icon-icon_whitechevronright"]/parent::a/@href').get('')
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page),
                                 callback=self.parse_tesco,
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
