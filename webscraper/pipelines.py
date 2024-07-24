import pymongo
from scrapy.exceptions import DropItem
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MongoDBPipeline:

    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE'),
            mongo_collection=crawler.settings.get('MONGODB_COLLECTION', 'items')
        )

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
            self.collection = self.db[self.mongo_collection]
            logging.info(f"Connected to MongoDB: {self.mongo_uri}, DB: {self.mongo_db}, Collection: {self.mongo_collection}")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def close_spider(self, spider):
        try:
            self.client.close()
            logging.info("Closed MongoDB connection")
        except Exception as e:
            logging.error(f"Failed to close MongoDB connection: {e}")

    def process_item(self, item, spider):
        required_fields = ['nkw', 'image_url', 'product_title', 'product_price', 'shipping_fee']
        
        for field in required_fields:
            if not item.get(field):
                logging.warning(f"Missing {field} in item: {item}")
                raise DropItem(f"Missing {field} in {item}")

        try:
            self.collection.update_one(
                {'_id': item['doc_id']},
                {'$set': {
                    'nkw': item['nkw'],
                    'image_url': item['image_url'],
                    'product_title': item['product_title'],
                    'product_price': item['product_price'],
                    'shipping_fee': item['shipping_fee']
                }},
                upsert=False
            )
            self.calculate_and_send_email(item)
            logging.info(f"Item saved to MongoDB and email sent if applicable: {item}")
            return item
        except Exception as e:
            logging.error(f"Failed to save item to MongoDB: {e}")
            raise e

    def calculate_and_send_email(self, item):
        amazon_item = self.collection.find_one({'nkw': item['nkw']})
        if not amazon_item:
            logging.warning(f"No matching Amazon item found for {item['nkw']}")
            return

        try:
            amazon_used_price = float(amazon_item.get('Buy Box Used: 180 days avg', '0').replace('£', '').replace(',', '').strip())
            fba_fee = float(amazon_item.get('FBA Fees:', '0').replace('£', '').replace(',', '').strip())
            referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
            referral_fee = amazon_used_price * referral_fee_percentage

            ebay_price = float(item['product_price'].replace('£', '').replace(',', '').strip())
            profit = ebay_price - amazon_used_price - fba_fee - referral_fee
            roi = profit / ebay_price if ebay_price else 0

            if roi > 0.5:
                self.send_email(
                    item['image_url'], item['nkw'], ebay_price,
                    amazon_item['image'], amazon_item['url'], amazon_used_price, roi
                )
        except Exception as e:
            logging.error(f"Error calculating ROI and sending email: {e}")

    def send_email(self, ebay_image, ebay_url, ebay_price, amazon_image, amazon_url, amazon_price, roi):
        try:
            sender_email = "xavusiness@gmail.com"
            receiver_email = "xavialerts@gmail.com"
            password = "tnthxazpsezagjdc"

            message = MIMEMultipart("alternative")
            message["Subject"] = "Alerta de ROI superior al 50%"
            message["From"] = sender_email
            message["To"] = receiver_email

            text = f"""\
            Alerta de ROI superior al 50%:
            - Imagen de eBay: {ebay_image}
            - URL de eBay: {ebay_url}
            - Precio de eBay: £{ebay_price}
            - Imagen de Amazon: {amazon_image}
            - URL de Amazon: {amazon_url}
            - Precio de Amazon: £{amazon_price}
            - ROI: {roi * 100}%
            """

            html = f"""\
            <html>
              <body>
                <h2>Alerta de ROI superior al 50%</h2>
                <p><strong>Imagen de eBay:</strong> <img src="{ebay_image}" width="100"></p>
                <p><strong>URL de eBay:</strong> <a href="{ebay_url}">{ebay_url}</a></p>
                <p><strong>Precio de eBay:</strong> £{ebay_price}</p>
                <p><strong>Imagen de Amazon:</strong> <img src="{amazon_image}" width="100"></p>
                <p><strong>URL de Amazon:</strong> <a href="{amazon_url}">{amazon_url}</a></p>
                <p><strong>Precio de Amazon:</strong> £{amazon_price}</p>
                <p><strong>ROI:</strong> {roi * 100}%</p>
              </body>
            </html>
            """

            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")

            message.attach(part1)
            message.attach(part2)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())

            logging.info("Email enviado exitosamente")
        except Exception as e:
            logging.error(f"Error al enviar email: {e}")
