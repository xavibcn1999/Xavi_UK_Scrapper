# -*- coding: utf-8 -*-

import scrapy
from scrapy.selector import Selector
from scrapy.utils.response import open_in_browser
from datetime import datetime
class etsy(scrapy.Spider):
    name = 'etsy'
    custom_settings = {'CONCURRENT_REQUESTS': 15,
                       # 'FEED_FORMAT': 'csv',
                       # 'FEED_URI': 'scraped_data/' + datetime.now().strftime('%Y_%m_%d__%H_%M') + 'etsy.csv',
                       }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }

    headers_new = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-csrf-token': '3:1649210134:5KZqaNcUTWAtb-ondy8-D_5odXwz:4ab70d3ac63f0dd86d9534a080dc222451e5d1f6824a591d3506eb2d191009b8',
        'x-detected-locale': 'GBP|en-GB|GB',
        'X-Page-GUID': 'effddd796db.581e63c17ecbd2d77dcf.00',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.etsy.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Referer': 'https://www.etsy.com/uk/search?q=candle&page=2&ref=pagination',
        'Connection': 'keep-alive',
        'Cookie': 'uaid=B3pitGDWsPsuI56WGH8-C1EdSL5jZACCJJ89vjC6Wqk0MTNFyUrJNT_dLNPPyaWivLDCKSrRzdIv3SPY3SzJ272kQqmWAQA.; user_prefs=189ZbIJJAnVIOb-q-FkaKeLhYVVjZACCJJ89vjA6WsndKUBJJ680J0dHKTVP191JSUcJRIBFjCAULiKWAQA.; fve=1649196109.0; exp_hangover=Nqnoew_iUXip7SH-Mu7MSECVBlZjZACCJJ89vhD6s1i1UkFqUVqMfnlqUnxiUUlmWmZyZmJOfE5iSWpecmV8oWG8kYGRkZJVWmJOcWotAwA.; ua=531227642bc86f3b5fd7103a0c0b4fd6; pla_spr=0; _gcl_au=1.1.1254372019.1649196112; _ga_KR3J610VYM=GS1.1.1649210134.2.0.1649210134.60; _ga=GA1.2.1058260606.1649196112; _tq_id.TV-27270909-1.a4d5=a7ae59a4a77d9b60.1649196113.0.1649196158..; __adal_id=ad7b2c14-ea4c-41b0-b1d8-51144d10e499.1649196113.1.1649196158.1649196113.0364a818-9d17-4c1e-97ec-65f1af936b6a; __adal_ca=so%3Ddirect%26me%3Dnone%26ca%3Ddirect%26co%3D%28not%2520set%29%26ke%3D%28not%2520set%29; __adal_cw=1649196113157; _pin_unauth=dWlkPU1EUmtORGt3TUdFdE4yRTRaaTAwWVRFMExUZzNOakl0WldaalptSmpNbVpoTVRVMA; _gid=GA1.2.1630315126.1649196114; last_browse_page=https%3A%2F%2Fwww.etsy.com%2Fuk%2Fshop%2FTheVPLcollective; _uetsid=ffd7f6c0b52b11ecae62c9983d176a77; _uetvid=ffd7ec80b52b11ecafae7bebb359fbdb; granify.uuid=7c4453ee-e3c8-41a7-8548-e24e9eb263d5; granify.session.QrsCf=1649210120987; uaid=VGFgMHAFlQapWkQvGn0tTXR9--tjZACCJF-ugzC6Wqk0MTNFyUrJzcjDqCAyKzjVItsgMDijoNgnzNCvKDXDJFfXWKmWAQA.',
        'TE': 'trailers'
    }


    def start_requests(self):
        yield scrapy.Request(
            url ='https://www.etsy.com/uk/search?q=candle&page=1&ref=pagination',
            callback=self.parse_page,
            headers=self.headers,

        )

    def parse_page(self, response):
        part_html = response.xpath('//script[contains(text(),"lazy")]/text()').get('')

        listing_ids = [str(i) for i in json.loads(part_html.split('lazy_loaded_listing_ids":')[1].split(']')[0] + ']')]
        ad_ids = [str(i) for i in json.loads(part_html.split('lazy_loaded_ad_ids":')[1].split(']')[0] + ']')]
        lazy_loaded_logging_keys = json.loads(part_html.split('lazy_loaded_logging_keys":')[1].split(']')[0] + ']')
        bucket_id = part_html.split('bucket_id":')[1].split(',')[0].strip('"')
        organic_listings_count = part_html.split('organic_listings_count":')[1].split(',')[0].strip('"')
        initial_current_page = part_html.split('initial_current_page":')[1].split(',')[0].strip('"')
        page_guid = response.text.split('page_guid":')[1].split(',')[0].strip('"')
        csrf = response.xpath('//meta[@name="csrf_nonce"]/@content').get('')

        product_links = response.xpath('.//a[@data-listing-id]/@data-listing-id').extract()

        for product in product_links:
            product_url = f"https://www.etsy.com/listing/{str(product)}"
            yield scrapy.Request(
                url = product_url,
                callback = self.parse_product,
                headers=self.headers
            )

        data = {
            'log_performance_metrics': 'true',
            'specs[listingCards][]': 'Search2_ApiSpecs_ListingCards',
            'specs[listingCards][1][listing_ids][]': listing_ids,
            'specs[listingCards][1][ad_ids][]': ad_ids,
            'specs[listingCards][1][logging_keys][]': lazy_loaded_logging_keys,
            'specs[listingCards][1][search_request_params][detected_locale][language]': 'en-GB',
            'specs[listingCards][1][search_request_params][detected_locale][currency_code]': 'GBP',
            'specs[listingCards][1][search_request_params][detected_locale][region]': 'GB',
            'specs[listingCards][1][search_request_params][locale][language]': 'en-GB',
            'specs[listingCards][1][search_request_params][locale][currency_code]': 'GBP',
            'specs[listingCards][1][search_request_params][locale][region]': 'GB',
            'specs[listingCards][1][search_request_params][name_map][query]': 'q',
            'specs[listingCards][1][search_request_params][name_map][query_type]': 'qt',
            'specs[listingCards][1][search_request_params][name_map][results_per_page]': 'result_count',
            'specs[listingCards][1][search_request_params][name_map][min_price]': 'min',
            'specs[listingCards][1][search_request_params][name_map][max_price]': 'max',
            'specs[listingCards][1][search_request_params][parameters][q]': 'candle',
            'specs[listingCards][1][search_request_params][parameters][page]': str(initial_current_page),
            'specs[listingCards][1][search_request_params][parameters][ref]': 'pagination',
            'specs[listingCards][1][search_request_params][parameters][utm_medium]': '',
            'specs[listingCards][1][search_request_params][parameters][utm_source]': '',
            'specs[listingCards][1][search_request_params][parameters][placement]': 'wsg',
            'specs[listingCards][1][search_request_params][parameters][page_type]': 'search',
            'specs[listingCards][1][search_request_params][parameters][referrer]': '',
            'specs[listingCards][1][search_request_params][parameters][bucket_id]': str(bucket_id),
            'specs[listingCards][1][search_request_params][parameters][user_id]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][app_os_version]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][app_version]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][currency]': 'GBP',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][device]': '1,0,0,0,0,0,0,0,0,0,0,0,0,0',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][environment]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][favorited]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][first_visit]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][http_referrer]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][language]': 'en-GB',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][last_login]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][purchases_awaiting_review]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][push_notification_settings]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][region]': 'GB',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][region_language_match]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][seller]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][shop_country]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][tier]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][time]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][time_since_last_login]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][time_since_last_purchase]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][user]': '0',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][exclude_groups]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][exclude_users]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][marketplace]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][user_agent]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][user_dataset]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][geoip]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][gdpr]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][email]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][request_restrictions]': '',
            'specs[listingCards][1][search_request_params][parameters][eligibility_map][marketing_channel]': '',
            'specs[listingCards][1][search_request_params][parameters][filter_distracting_content]': 'true',
            'specs[listingCards][1][search_request_params][parameters][spell_correction_via_mmx]': 'true',
            'specs[listingCards][1][search_request_params][parameters][interleaving_option]': '',
            'specs[listingCards][1][search_request_params][parameters][should_pass_user_location_to_thrift]': 'true',
            'specs[listingCards][1][search_request_params][parameters][result_count]': '48',
            'specs[listingCards][1][search_request_params][user_id]': '',
            'specs[listingCards][1][is_mobile]': 'false',
            'specs[listingCards][1][organic_listings_count]':str(organic_listings_count),
            'specs[listingCards][1][pred_score]': '',
            'view_data_event_name': 'search_lazy_loaded_cards_specview_rendered',
        }
        self.headers_new['cookie'] = '; '.join([i.decode().split(';')[0] for i in dict(response.headers)[b'Set-Cookie']])
        self.headers_new['x-csrf-token'] = csrf
        self.headers_new['X-Page-GUID'] = page_guid

        yield scrapy.FormRequest(
            url= 'https://www.etsy.com/api/v3/ajax/bespoke/member/neu/specs/listingCards',
            callback=self.parse_details,
            # body=json.dumps(data),
            formdata=data,
            headers=self.headers_new
        )

    def parse_details(self,response):
        details_json = json.loads(response.text)

        listings = Selector(text = details_json['output']['listingCards'])

        product_links = listings.xpath('.//a[@data-listing-id]/@data-listing-id').extract()

        # links = response.xpath('//div[@data-search-results-region]//a[@data-listing-id]/@href').extract()

        listings.xpath('.//div[@data-search-results-region]//a[@data-listing-id]/@href').extract()
        for product in product_links:
            product_url = f"https://www.etsy.com/listing/{str(product)}"
            yield scrapy.Request(
                url = product_url,
                callback = self.parse_product,
                headers=self.headers
            )

    def parse_product(self,response):

        seller_link = response.xpath('//a[contains(@aria-label,"View more products from shop owner")]/@href').get('').split('?')[0] + '/sold'
        yield scrapy.Request(
            url = seller_link,
            callback = self.parse_seller,
            meta = {
                'item_count' : {},
                'seller_link' :  response.xpath('//a[contains(@aria-label,"View more products from shop owner")]/@href').get('').split('?')[0]
            },
            headers=self.headers
        )


    def parse_seller(self,response):

        if response.meta['item_count'] == {}:
            rating = response.xpath('//input[@name="rating"]/@value').get('')
            reviewCount = response.text.split('"reviewCount":')[1].split(',')[0].replace('"','').replace('}','').strip()
            total_sales = response.xpath('//div[contains(text(),"Sales")]/text()').get('').replace('Sales','').strip()
            seller_name = response.xpath('//h1/div/text()').get('').strip()


        else:
            rating = response.meta['rating']
            reviewCount = response.meta['reviewCount']
            total_sales = response.meta['total_sales']
            seller_name = response.meta['seller_name']
        seller_link = response.meta['seller_link']

        item_count = response.meta['item_count']

        listings = response.xpath('//a[contains(@class,"listing-link")]')

        for listing in listings:
            listing_name = listing.xpath('./@title').get('')
            if item_count.get(listing_name,{}).get('count',''):
                item_count[listing_name]['count'] += 1
            else:
                item_count[listing_name] = {
                    'count' : 1,
                    'listing_url' : listing.xpath('.//img/@src').get('')
                }


        next_page = response.xpath('//span[contains(text(),"Next page")]/parent::a/@href').get('')
        if next_page:
            yield scrapy.Request(
                url = next_page,
                callback = self.parse_seller,
                meta = {'rating':rating,'reviewCount':reviewCount,'item_count':item_count,'total_sales':total_sales,'seller_name':seller_name,'seller_link':seller_link},
                headers=self.headers
            )

        if not next_page:

            for i,j in item_count.items():

                item = {
                    'Seller Name' : seller_name,
                    'Product Name' : i,
                    'Total Sales' : total_sales,
                    'Product Sales' : j['count'],
                    'Review' : rating,
                    'Total Reviews' : reviewCount,
                    'Product Image' : j['listing_url'],
                    'Seller URL' : seller_link
                }

                yield item







