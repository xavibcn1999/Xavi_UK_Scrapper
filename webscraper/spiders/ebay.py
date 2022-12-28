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



class ebay(scrapy.Spider):
    name = 'ebay'
    custom_settings = {'CONCURRENT_REQUESTS': 7,
                       'FEED_FORMAT': 'csv',
                       'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + 'ebay.csv',
                       'RETRY_TIMES': 15,
                       'COOKIES_ENABLED': True,
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

    def __init__(self, url=None, *args, **kwargs):
        super(ebay, self).__init__(*args, **kwargs)
        self.url = url

    # proxy = ''

    # def __init__(self, cat=None,id =None, *args, **kwargs):
    #     super(ebay, self).__init__(*args, **kwargs)
    #     self.cat = cat
    #     if not id:
    #         self.id = '788'
    #     else:
    #         self.id  = str(id)

    # file = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'

    def start_requests(self):

        df = pd.read_csv(self.url)

        urls = df['url'].tolist()

        # for url in urls:
                
        #     yield scrapy.Request(
        #         url=url,
        #         headers=header.generate(),
        #         callback=self.parse,
        #         meta={
        #             'url': url,
        #             'proxy': self.proxy
        #         }
        #     )
        ranges = {

            '0-1000': 1,
            # '500-1500': 1,
            # '1500-2000': 5,
    

        }
        

        # urls = [
        #     'https://www.ebay.co.uk/b/Fiction-Non-Fiction-Books/261186/bn_450928?Genre=Art%2520%2526%2520Culture&rt=nc&_udlo=12.01&_udhi=12.02&&LH_ItemCondition=2750%7C4000%7C5000%7C6000%7C10&mag=1',
        #      'https://www.ebay.co.uk/b/Fiction-Non-Fiction-Books/261186/bn_450928?Genre=Art%2520%2526%2520Culture&rt=nc'
        # ]

        # final_urls = [
        #     # 'https://www.ebay.co.uk/b/Fiction-Non-Fiction-Books/261186/bn_450928?Genre=Art%2520%2526%2520Culture&rt=nc&_udlo=12.01&_udhi=12.02&&LH_ItemCondition=2750%7C4000%7C5000%7C6000%7C10&mag=1',
        #      'https://www.ebay.co.uk/b/Fiction-Non-Fiction-Books/261186/bn_450928?Genre=Art%2520%2526%2520Culture&rt=nc'
        # ]

        final_urls = []

        
        # final_urls = []

        for url in urls:

            if '_uldo' in url or '_udhi' in url:
                final_urls.append(url)
                continue

            # add over 2000

            final_urls.append(url + '&_udlo=1000')

            for item in ranges:

                start = int(item.split('-')[0])
                end = int(item.split('-')[-1])
                counter = ranges[item]
                while start < end:
                    try:

                        url = url + '&_udlo=' + str(start) + '&_udhi=' + str(start + counter)

                        final_urls.append(url)
                        # self.logger.info(url)
                  
                    except Exception as e:
                        print(e)


                    start += counter

        for url in final_urls:

            yield scrapy.Request(
                url=url,
                # headers=self.headers,
                headers=header.generate(),
                callback=self.parse,
                meta={
                    'url': url,
                    'proxy': self.proxy,
                }
            )



        # yield scrapy.Request(

        #     url = 'https://www.ebay.co.uk/p/10046645292',
        #     # headers=self.headers,
        #     headers=header.generate(),
        #     callback=self.parse_item,
        #     meta={
        #         # 'url': url,
        #         'proxy': self.proxy,
        #     }
        # )

   

    def parse(self, response):

        if 'captcha' in response.url:
            self.logger.info('Captcha found')
            yield scrapy.Request(
                url=response.meta['url'],
                # headers=self.headers,
                headers=header.generate(),
                callback=self.parse,
                dont_filter=True,
                meta={
                    'proxy': self.proxy,
                    'url': response.meta['url'],
                }
            )
            return

        
        links = response.xpath('//a[@class="s-item__link"]/@href').getall()

        for link in links:
            yield scrapy.Request(

                # url = 'https://www.ebay.co.uk/itm/304337734556?mkcid=16&mkevt=1&mkrid=711-127632-2357-0&ssspo=yzX_Fr4wRbq&sssrc=2349624&ssuid=dkezgjylqns&var=&widget_ver=artemis&media=COPY',
                url=link,
                # headers=self.headers,
                headers=header.generate(),
                callback=self.parse_item,
                meta={
                    'proxy': self.proxy,
                    'url': link,
                }
            )

        
        # next_page = response.xpath('//a[@aria-label="Go to next search page"]/@href').get('')

        next_page_links = response.xpath('//a[@class="pagination__item"]/@href').getall()


        for page in next_page_links:
            yield scrapy.Request(
                url=response.urljoin(page),
                # headers=self.headers,
                headers=header.generate(),
                callback=self.parse,
                meta={
                    'url': page,
                    'proxy': self.proxy,
                }
            )
   

    
    def parse_item(self, response):
        

        if 'captcha' in response.url:
            self.logger.info('Captcha found')
            yield scrapy.Request(
                url=response.meta['url'],
                # headers=self.headers,
                headers=header.generate(),
                callback=self.parse_item,
                dont_filter=True,
                meta={
                    'proxy': self.proxy,
                    'url': response.meta['url'],
                }
            )
            return


        title = ' '.join([i.strip() for i in response.xpath('//h1//text()').getall() if i.strip()])

        images = ';'.join([i.replace('-l64.jpg', '-l640.jpg') for i in response.xpath('//div[@class="ux-image-filmstrip-carousel"]//img/@src').getall()])

        if not images:
            images = ';'.join([i.replace('-l64.jpg', '-l640.jpg') for i in response.xpath('//div[@id="primary-gallery"]//img/@src').getall() if'/images/' in i])

        if not images:
            images = response.xpath('//meta[@property="og:image"]/@content').get('')


        # Price Section

        price = response.xpath('//span[@itemprop="price"]//text()').get('')

        if not price:
            price = response.xpath('//span[@class="item-price "]//text()').get('')

        # ISBN Section

        isbn13 = response.xpath('//div[@class="s-name" and contains(text(),"ISBN-13")]//following-sibling::div//text()').get('')

        if not isbn13:
            isbn13 = response.xpath('//div[@class="ux-labels-values col-12 ux-labels-values--isbn-13"]//div[@class="ux-labels-values__values-content"]//span//text()').get('')


        isbn10 = response.xpath('//div[@class="s-name" and contains(text(),"ISBN-10")]//following-sibling::div//text()').get('')

        if not isbn10:
            isbn10 = response.xpath('//div[@class="ux-labels-values col-12 ux-labels-values--isbn-10"]//div[@class="ux-labels-values__values-content"]//span//text()').get('')
       

        if not isbn13 and not isbn10:
            isbn =response.xpath('//span[@class="ux-textspans" and text() = "ISBN:"]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')

        
        isbn13 = isbn13 if isbn13 else isbn


        # item_weight Section

        item_weight = response.xpath('//div[@class="s-name" and contains(text(),"Item Weight")]//following-sibling::div//text()').get('')

        if not item_weight:
            item_weight = response.xpath('//div[@class="ux-labels-values col-12 ux-labels-values__column-last-row ux-labels-values--itemWeight"]//div[@class="ux-labels-values__values-content"]//span//text()').get('')

        if not item_weight:
            item_weight = response.xpath('//span[@class="ux-textspans" and contains(text(),"Weight")]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')




        # shipping_cost Section


        shipping_cost = response.xpath('//span[@class="logistics-cost"]//text()').get('')

        if not shipping_cost:
            shipping_cost = response.xpath('//span[@class="ux-textspans" and contains(text(),"Postage:")]/ancestor::div[@class="ux-labels-values__labels col-3"]/following-sibling::div//span//text()').get('') 


        # condition Section

        condition_variable = response.xpath('//span[contains(text(),"Condition:")]/parent::div[@class="d-item-condition-label"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')

        if not condition_variable:
            condition_variable = response.xpath('//div[@class="s-name" and contains(text(),"Condition")]//following-sibling::div//text()').get('')

        if not condition_variable:
            condition_variable = ' '.join(response.xpath('//span[@class="ux-textspans" and text() = "Condition:"]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').getall())

        

        
        condition_variable = condition_variable.split(':')[0]

        if not condition_variable:
            condition_variable = response.xpath('//h2[@class="theme-title"]//text()').get('').split(':')[0]

        # format Section

        format = response.xpath('//span[@class="ux-textspans" and text() = "Format:"]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')


        if not format:
            format = response.xpath('//div[@class="s-name" and contains(text(),"Format")]//following-sibling::div//text()').get('')


        # EAN Section

        ean = response.xpath('//span[@class="ux-textspans" and text() = "EAN:"]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')

        if not ean:
            ean = response.xpath('//div[@class="s-name" and contains(text(),"EAN")]//following-sibling::div//text()').get('')





        # UPC Section
        upc = response.xpath('//span[@class="ux-textspans" and text() = "UPC:"]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')

        if not upc:
            upc = response.xpath('//div[@class="s-name" and contains(text(),"UPC")]//following-sibling::div//text()').get('')

        
        # GTIN Section

        gtin = response.xpath('//span[@class="ux-textspans" and text() = "GTIN:"]/ancestor::div[@class="ux-labels-values__labels"]/following-sibling::div//span[@class="ux-textspans"]//text()').get('')

        if not gtin:
            gtin = response.xpath('//div[@class="s-name" and contains(text(),"GTIN")]//following-sibling::div//text()').get('')



        


        item = {
            '01_Book Title': title,
            '02_Product URL': response.url.split('?')[0],
            '03_Product Images': images,
            '04_Price': price,
            '05_Shipping Price': shipping_cost,
            '06_Weight': item_weight,
            '07_Condition': condition_variable,
            '08_Format': format,
            '10_ISBN-10': "'" + isbn10,
            '09_ISBN-13': "'" + isbn13,
            '11_EAN': "'" + ean,
            '12_GTIN': "'" + gtin,
            '13_UPC': "'" + upc,
        }





        yield item






    
       
