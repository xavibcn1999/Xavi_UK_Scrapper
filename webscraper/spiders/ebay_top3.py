# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
import pandas as pd
from fake_headers import Headers
import smtplib

from scrapy.utils.response import open_in_browser
#import open_in_browser(response)
header = Headers(browser="chrome",  # Generate only Chrome UA
                 os="win",  # Generate ony Windows platform
                 headers=True)



class ebay_top3(scrapy.Spider):
    name = 'ebay_top3'
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

    def __init__(self, url=None, *args, **kwargs):
        super(ebay_top3, self).__init__(*args, **kwargs)
        self.url = url

   
    # file = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'
    # url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTeZxZduOfcazmDjKEGfYmHpJD1J1BGODjyAF91v8DMRMgR5fZQc9CAUPXuTQQMMAQHNyxTKTsLce04/pub?gid=0&single=true&output=csv'
    
    # url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR7IVO_B95bONHJX6ahtm9K8INz0Tt1bajd9EiqCYfpHk7b68UmlxvXxe7Gw1dX6EuSVFPhc8fhM4NI/pub?gid=0&single=true&output=csv'
    def start_requests(self):

        df = pd.read_csv(self.url)

        url_list = [i for i in df['url'].tolist() if i.strip()]

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
        nkw = response.meta['nkw']

        listings = response.xpath('//ul//div[@class="s-item__wrapper clearfix"]')[:3]

        for rank, listing in enumerate(listings):

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

            if seller_name:
                seller_name = seller_name.strip()
            item = {
                'URL': response.url,
                'NKW': "'" + nkw,
                'Image URL': image,
                'Product Title': title,
                'Product Price': price,
                'Shipping Fee': shipping_cost,
                'Postion': rank + 1,
                'Item Number': item_number,
                'Seller Name': seller_name,


            }

            yield item

# ... (todo lo demás permanece igual) ...

    def closed(self, reason):
        # Esta función se ejecuta cuando el spider se cierra
        self.send_email()

    def send_email(self):
    # Datos del correo
    sender_email = "xavusiness@gmail.com"
    receiver_email = "xaviergomezvidal@gmail.com"
    password = "api-258C6D46609A11EEBD95F23C91C88F4E"
    subject = "Scrapy Alert"
    body = "The spider has finished its job."

    # Construyendo el correo
    message = f"Subject: {subject}\n\n{body}"

    try:
        # Enviando el correo
        with smtplib.SMTP_SSL("mail.smtp2go.com", 465) as server:
            server.login("AlertsZyte", "u3G1ZYGI2lCAl3Lo")
            server.sendmail(sender_email, receiver_email, message)
        print("Correo enviado exitosamente")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")        

        

      
