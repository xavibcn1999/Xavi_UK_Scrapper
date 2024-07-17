from fake_headers import Headers
import scrapy
import json
from pymongo import MongoClient


header = Headers(browser="chrome",  # Generate only Chrome UA
                 os="win",  # Generate ony Windows platform
                 headers=True)


class Spider_Search(scrapy.Spider):
    name = 'Spider_Search'
    custom_settings = {
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': False,
        'FEED_EXPORT_ENCODING': "utf-8"
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

    proxy = 'http://xavigv:GOkNQBPK2DplRGqw_country-UnitedStates@proxy.packetstream.io:31112'

    def connect(self):
        client = MongoClient('mongodb+srv://xavidb:WrwQeAALK5kTIMCg@serverlessinstance0.lih2lnk.mongodb.net/')
        self.db = client["Flip_Booster"]
        self.collection_ebay = self.db['Search_List_E']
        self.collection_A = self.db['Search_List_A']

        print("connected successfully!")

    def ebay_retrieve(self, start, end):
        left_urls = []
        data_urls = list(self.collection_A.find({"id_count": {"$gte": int(start), "$lte": int(end)}}))
        for data_urls_loop in data_urls:
            left_urls.append(data_urls_loop['url'])

        return left_urls

    def __init__(self, url=None, *args, **kwargs):
        super(Spider_Search, self).__init__(*args, **kwargs)

    def start_requests(self):
        chunk_start = getattr(self, 'chunk', None)
        print('-------chunks', chunk_start)
        start = int(chunk_start.split(',')[0].strip())
        end = int(chunk_start.split(',')[1].strip())
        self.connect()
        print('start-------', start)
        print('end-------', end)

        if start is not None and end is not None:
            data = self.ebay_retrieve(start, end)
            url_list = data
            print('i am in start request')
            for request_url in url_list:
                try:
                    nkw = request_url.split('_nkw=')[1].split('&')[0]
                except:
                    nkw = ''
                yield scrapy.Request(url=request_url, callback=self.parse, headers=self.headers,
                                     meta={'proxy': self.proxy,
                                           'nkw': nkw
                                           })

    def parse(self, response):
        print('i am in parse')
        nkw = response.meta['nkw']

        listings = response.xpath('//ul//div[@class="s-item__wrapper clearfix"]')[:2]

        for rank, listing in enumerate(listings):
            try:
                if 'best offer' in listing.css('span.s-item__purchase-options.s-item__purchaseOptions ::text').get().lower():
                    best_offer = 'yes'
                else:
                    best_offer = 'no'

            except:
                best_offer = 'no'

            link = listing.xpath('.//a/@href').get('')
            title = listing.xpath('.//span[@role="heading"]/text()').get('')

            price = listing.xpath('.//span[@class="s-item__price"]/text()').get('')

            image = listing.xpath('.//div[contains(@class,"s-item__image")]//img/@src').get('')

            image = image.replace('s-l225.webp', 's-l500.jpg')

            shipping_cost = listing.xpath('.//span[@class="s-item__shipping s-item__logisticsCost"]/text()').get('')
            if not shipping_cost:
                shipping_cost = listing.xpath('.//span[@class="s-item__dynamic s-item__freeXDays"]//text()').get('')
            try:
                item_number = listing.xpath('.//a/@href').get('').split('/itm/')[1].split('?')[0]
            except:
                item_number = ''
            seller_name = listing.xpath('.//*[@class="s-item__seller-info-text"]//text()').get('').split('(')[0]

            try:
                condition = listing.css('div.s-item__subtitle span.SECONDARY_INFO ::text').get().lower()
            except:
                condition = ""

            if condition == 'brand new':
                condition2 = "new"
            else:
                condition2 = 'used'

            if seller_name:
                seller_name = seller_name.strip()
            item = {
                'url': response.url,
                'NKW': "'" + nkw,
                'Image URL': image,
                'Product Title': title,
                'Product Price': price,
                'Shipping Fee': shipping_cost,
                'Postion': rank + 1,
                'Item Number': item_number,
                'Seller Name': seller_name,
                'condition': condition2,
                'best_offers': best_offer

            }

            yield scrapy.Request(url=link, callback=self.next_parse, meta={'item_data': item})

    def next_parse(self, response):
        item_parse = response.meta['item_data']
        try:
            cat_subcat = json.loads([v for v in response.css('script[type="application/ld+json"] ::text').extract() if
                                     'BreadcrumbList' in v][0])['itemListElement'][1:]
        except:
            cat_subcat = ""

        try:
            item_parse['Date Listed'] = ''.join(list(set(response.css(
                'div.ux-layout-section__textual-display--revisionHistory > span ::text').extract()))).replace(
                'Last updated on', "")
        except:
            item_parse['Date Listed'] = ""

        try:
            item_parse['Seller Feedback Count'] = response.css(
                'h2.fdbk-detail-list__title span.SECONDARY ::text').get().replace("(", "").replace(")", "")
        except:
            item_parse['Seller Feedback Count'] = ""
        try:
            item_parse['Seller Positive Feedback Percentage'] = \
            [v for v in response.css('li.ux-seller-section__item span.ux-textspans ::text').extract() if
             'positive Feedback' in v][0].split('positive Feedback')[0].strip()
        except:
            item_parse['Seller Positive Feedback Percentage'] = ""

        try:
            item_parse['Category'] = cat_subcat[0]['name']
        except:
            item_parse['Category'] = ""
        try:
            item_parse['Subcategory'] = cat_subcat[1]['name']
        except:
            item_parse['Subcategory'] = ""
        try:
            if "days return. Buyer pays for return postage" in "".join(
                    response.css('div.ux-labels-values--returns ::text').extract()):
                item_parse['Returns_Accepted'] = 'yes'
        except:
            item_parse['Returns_Accepted'] = "no"
        try:
            item_parse['subcondition'] = response.css(
                'div.x-item-condition-text span.ux-textspans ::text').get().lower()
        except:
            item_parse['subcondition'] = ""
        try:
            item_parse['quantity_remaining'] = response.css('div.d-quantity__availability span ::text').get()
        except:
            item_parse['quantity_remaining'] = ""
        item_parse['product_url'] = response.url
        main_url = item_parse['url']
        del item_parse['url']

        self.collection_ebay.insert_one(item_parse)

