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
        try:
            client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/')
            self.db = client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            self.collection_A = self.db['Search_uk_A']
            self.logger.info("Conexión a MongoDB establecida.")
        except Exception as e:
            self.logger.error(f"Error al conectar a MongoDB: {e}")

    def start_requests(self):
        data_urls = list(self.collection_E.find({'url': {'$ne': ''}}))

        if not data_urls:
            self.logger.warning("No se encontraron URLs en la colección Search_uk_E.")
            return

        self.logger.info(f"Se encontraron {len(data_urls)} URLs para procesar.")

        for data_urls_loop in data_urls:
            url = data_urls_loop.get('url', '').strip()
            nkw = data_urls_loop.get('ASIN', '').strip("'")

            if url:
                self.logger.info(f"Generando solicitud para URL: {url}")
                yield scrapy.Request(url=url, callback=self.parse, headers=self.headers,
                                     meta={'proxy': self.proxy, 'nkw': nkw})
            else:
                self.logger.warning("URL vacía encontrada en la colección Search_uk_E.")

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

            # Actualizar el documento existente en Search_uk_E con los nuevos datos, sin sobrescribir la columna URL
            self.collection_E.update_one(
                {'ASIN': nkw},
                {'$set': {
                    'Image URL': image,
                    'Product Title': title,
                    'Product Price': price,
                    'Shipping Fee': shipping_cost,
                    'Seller Name': seller_name,
                }}
            )

            # Calcular el ROI y enviar el email si es mayor al 50%
            try:
                ebay_price = float(price.replace('£', '').replace(',', ''))
                amazon_item = self.collection_A.find_one({'ASIN': nkw})

                if amazon_item:
                    amazon_used_price = float(amazon_item['Buy Box Used: 180 days avg'].replace('£', '').replace(',', ''))
                    fba_fee = float(amazon_item['FBA Fees:'].replace('£', '').replace(',', ''))
                    referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
                    referral_fee = amazon_used_price * referral_fee_percentage

                    profit = ebay_price - amazon_used_price - fba_fee - referral_fee
                    roi = (profit / ebay_price) * 100 if ebay_price else 0

                    if roi > 50:
                        self.send_email(
                            ebay_image=image,
                            amazon_image=amazon_item['Image'],
                            amazon_title=amazon_item['Title'],
                            roi=roi,
                            amazon_used_price=amazon_used_price,
                            ebay_price=ebay_price,
                            amazon_url=amazon_item['URL: Amazon'],
                            ebay_url=response.url
                        )
            except Exception as e:
                self.logger.error(f"Error al calcular el ROI o enviar el email: {e}")

            count += 1

            if count >= 2:
                break

    def send_email(self, ebay_image, amazon_image, amazon_title, roi, amazon_used_price, ebay_price, amazon_url, ebay_url):
        try:
            sender_email = "tuemail@gmail.com"
            receiver_email = "destinatario@gmail.com"
            password = "tucontraseña"

            message = MIMEMultipart("alternative")
            message["Subject"] = f"Alerta de ROI > 50%: {amazon_title}"
            message["From"] = sender_email
            message["To"] = receiver_email

            html = f"""
            <html>
            <body>
                <h2>Alerta de ROI > 50%</h2>
                <p><b>Amazon Title:</b> {amazon_title}</p>
                <p><b>ROI:</b> {roi}%</p>
                <p><b>Amazon Used Price (180 days avg):</b> £{amazon_used_price}</p>
                <p><b>eBay Price:</b> £{ebay_price}</p>
                <p><b>Amazon URL:</b> <a href="{amazon_url}">{amazon_url}</a></p>
                <p><b>eBay URL:</b> <a href="{ebay_url}">{ebay_url}</a></p>
                <p><img src="{amazon_image}" alt="Amazon Image" width="150"><img src="{ebay_image}" alt="eBay Image" width="150"></p>
            </body>
            </html>
            """

            part = MIMEText(html, "html")
            message.attach(part)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as
