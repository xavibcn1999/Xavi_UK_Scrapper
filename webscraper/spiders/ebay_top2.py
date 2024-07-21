import scrapy
from pymongo import MongoClient
from datetime import datetime
from fake_headers import Headers
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

header = Headers(browser="chrome", os="win", headers=True)

class EbayTop2Spider(scrapy.Spider):
    name = 'ebay_top2'
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'FEED_FORMAT': 'csv',
        'FEED_URI': datetime.now().strftime('%Y_%m_%d__%H_%M') + '_ebay.csv',
        'RETRY_TIMES': 15,
        'COOKIES_ENABLED': True,
        'FEED_EXPORT_ENCODING': "utf-8"
    }

    headers = {
        'authority': 'www.ebay.com',
        'upgrade-insecure-requests': '1',
        'user-agent': header.generate()['User-Agent'],
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-gpc': '1',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9',
    }

    proxy = 'http://xavigv:ee3ee0580b725494_country-UnitedKingdom@proxy.packetstream.io:31112'

    def __init__(self, *args, **kwargs):
        super(EbayTop2Spider, self).__init__(*args, **kwargs)
        self.connect()

    def connect(self):
        client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/')
        self.db = client["Xavi_UK"]
        self.collection_E = self.db['Search_uk_E']
        self.collection_A = self.db['Search_uk_A']

    def start_requests(self):
        data_urls = list(self.collection_E.find({'url': {'$ne': ''}}))

        for data_urls_loop in data_urls:
            url = data_urls_loop.get('url', '').strip()
            nkw = data_urls_loop.get('ASIN', '').strip("'")

            yield scrapy.Request(url=url, callback=self.parse, headers=self.headers,
                                 meta={'proxy': self.proxy, 'nkw': nkw})

    def parse(self, response):
        nkw = response.meta['nkw']
        listings = response.xpath('//ul//div[@class="s-item__wrapper clearfix"]')

        count = 0

        for listing in listings:
            if listing.xpath('.//li[contains(@class,"srp-river-answer--REWRITE_START")]').get():
                self.logger.info("Found international sellers separator. Stopping extraction for this URL.")
                break

            if listing.xpath('.//span[@class="s-item__location s-item__itemLocation"]').get():
                self.logger.info("Skipping listing with location info.")
                continue

            link = listing.xpath('.//a/@href').get('')
            title = listing.xpath('.//span[@role="heading"]/text()').get('')
            price = listing.xpath('.//span[@class="s-item__price"]/text()').get('')
            if not price:
                price = listing.xpath('.//span[@class="s-item__price"]/span/text()').get('')

            image = listing.xpath('.//div[contains(@class,"s-item__image")]//img/@src').get('')
            image = image.replace('s-l225.webp', 's-l500.jpg')

            shipping_cost = listing.xpath('.//span[contains(text(),"postage") or contains(text(),"shipping")]/text()').re_first(r'\+\s?[£$€][\d,.]+')
            if not shipping_cost:
                shipping_cost = listing.xpath('.//span[contains(@class,"s-item__shipping") or contains(@class,"s-item__logisticsCost") or contains(@class,"s-item__freeXDays")]/text()').re_first(r'\+\s?[£$€][\d,.]+')

            seller_name = listing.xpath('.//span[@class="s-item__seller-info-text"]//text()').get('')
            if not seller_name:
                seller_name = listing.xpath('.//span[@class="s-item__seller-info"]//text()').get('')

            if seller_name:
                seller_name = seller_name.split('(')[0].strip()
            else:
                self.logger.warning(f"Could not extract seller name for listing: {link}")

            ebay_item = {
                'URL': response.url,
                'NKW': nkw,
                'Image URL': image,
                'Product Title': title,
                'Product Price': price,
                'Shipping Fee': shipping_cost,
                'Seller Name': seller_name,
            }

            # Actualizar el documento existente en Search_uk_E con los nuevos datos, sin sobrescribir la columna URL
            self.collection_E.update_one(
                {'ASIN': nkw},
                {'$set': ebay_item}
            )

            # Buscar el artículo correspondiente en la tabla de Amazon
            amazon_item = self.collection_A.find_one({'ASIN': nkw})
            if amazon_item:
                self.process_and_send(ebay_item, amazon_item)

            count += 1

            if count >= 2:
                break

    def process_and_send(self, ebay_item, amazon_item):
        try:
            ebay_price = float(ebay_item['Product Price'].replace('£', '').replace(',', '').strip())
            amazon_used_price = float(amazon_item['Buy Box Used 180 days avg'])
            fba_fee = float(amazon_item['FBA Fee'])
            referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
            referral_fee = amazon_used_price * referral_fee_percentage

            profit = ebay_price - amazon_used_price - fba_fee - referral_fee
            roi = profit / ebay_price if ebay_price else 0

            if roi > 0.5:
                subject = "Nuevo artículo con ROI superior al 50%"
                body = f"""
                <html>
                <body>
                    <h2>Detalles del artículo:</h2>
                    <p><strong>Imagen de eBay:</strong></p>
                    <img src="{ebay_item['Image URL']}" alt="eBay Image" style="width:100px;"><br>
                    <p><strong>Imagen de Amazon:</strong></p>
                    <img src="{amazon_item['Image']}" alt="Amazon Image" style="width:100px;"><br>
                    <p><strong>Título de Amazon:</strong> {amazon_item['Title']}</p>
                    <p><strong>ROI:</strong> {roi * 100:.2f}%</p>
                    <p><strong>Precio en Amazon (180 días promedio usado):</strong> £{amazon_used_price}</p>
                    <p><strong>Precio en eBay:</strong> £{ebay_price}</p>
                    <p><strong>Enlace de Amazon:</strong> <a href="{amazon_item['URL']}">Amazon Link</a></p>
                    <p><strong>Enlace de eBay:</strong> <a href="{ebay_item['URL']}">eBay Link</a></p>
                </body>
                </html>
                """
                self.send_email(subject, body, "xavialerts@gmail.com")
        except KeyError as e:
            print(f"Clave faltante {e} en artículo de eBay: {ebay_item}")

    def send_email(self, subject, body, to_email):
        from_email = "xavusiness@gmail.com"
        password = "!O4zv9eJH7xLIzj"

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
