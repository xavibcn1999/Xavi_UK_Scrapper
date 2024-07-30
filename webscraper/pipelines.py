import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient
from bson import ObjectId
import logging
from datetime import datetime, timedelta
import urllib.parse

class MongoDBPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.mongo_uri = settings.get('MONGO_URI')
        self.mongo_db = settings.get('MONGO_DATABASE')
        self.collection_name_e = 'ebay_items'
        self.collection_name_a = 'Search_uk_A'
        self.collection_name_cache = 'Search_uk_Cache'
        self.gmail_accounts = [
            {"email": "xavusiness@gmail.com", "password": "tnthxazpsezagjdc"},
            {"email": "xaviergomezvidal@gmail.com", "password": "cqpbqwvqbqvjpmly"},
            {"email": "xavigv77@gmail.com", "password": "crdgantmezylfjyq"},
            {"email": "xavigv0408@gmail.com", "password": "excohgpjkrbyvbtn"},
            {"email": "xavigomezvidal@gmail.com", "password": "lunuwnctjjsbchzx"},
            {"email": "xavibcn1999@gmail.com", "password": "vcjlpcfemckrpsvm"}
        ]
        self.current_account = 0
        self.exchange_rate = 1.29

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_ebay = self.db[self.collection_name_e]
        self.collection_a = self.db[self.collection_name_a]
        self.collection_cache = self.db[self.collection_name_cache]
        self.collection_search_uk_e = self.db['Search_uk_E']

    def close_spider(self, spider):
        self.clean_cache()
        self.client.close()

    def clean_cache(self):
        current_date = datetime.utcnow()
        result = self.collection_cache.delete_many({'expiry_date': {'$lt': current_date}})
        logging.info(f"Cache cleaned, {result.deleted_count} expired items removed.")

    def process_item(self, item, spider):
        try:
            item['product_price'] = self.convert_price(item['product_price'])
            item['shipping_fee'] = self.convert_price(item['shipping_fee']) if item.get('shipping_fee') else 0.0
        except Exception as e:
            logging.error(f"Error converting prices: {e}")
            item['product_price'] = 0.0
            item['shipping_fee'] = 0.0

        if '_id' not in item:
            logging.error("El item no tiene '_id'")
            return item

        item['item_number'] = item.get('item_number', '')
        item['product_url'] = item.get('product_url', '')

        # Extract search_key from the Search_uk_E collection
        search_key = self.get_search_key_from_db(item['_id'])
        item['search_key'] = search_key
        logging.info(f"Extracted search_key: {search_key}")

        self.collection_ebay.update_one({'_id': item['_id']}, {'$set': item}, upsert=True)
        self.calculate_and_send_email(item)
        return item

    def convert_price(self, price_str):
        if isinstance(price_str, str):
            price_str = price_str.replace('£', '').replace('US $', '').replace('+', '').replace(',', '').strip()
            if 'US' in price_str:
                return float(price_str) / self.exchange_rate
        return float(price_str)

    def get_search_key_from_db(self, item_id):
        search_uk_e_item = self.collection_search_uk_e.find_one({'_id': item_id})
        if search_uk_e_item:
            return search_uk_e_item.get('search_key', '')
        return ''

    def calculate_and_send_email(self, item):
        try:
            ebay_price = round(item['product_price'] + item['shipping_fee'], 2)
            logging.info(f"Precio del producto en eBay: {item['product_price']}")
            logging.info(f"Costo de envío en eBay: {item['shipping_fee']}")
            logging.info(f"Precio de eBay (producto + envío): {ebay_price}")
            logging.debug(f"ebay_price calculado: {ebay_price}")

            search_key = item.get('search_key')
            logging.info(f"Search key: {search_key}")
            
            if not search_key:
                logging.warning("Search key is empty, cannot proceed with ROI calculation")
                return

            amazon_item = None
            if search_key.isdigit() and len(search_key) == 10:
                amazon_item = self.collection_a.find_one({'ASIN': search_key})
            elif len(search_key) == 13 and search_key.isdigit():
                amazon_item = self.collection_a.find_one({'ISBN13': search_key})
            else:
                # Try an exact match first
                amazon_item = self.collection_a.find_one({'Title': search_key})
                if not amazon_item:
                    # If no exact match, try a partial match
                    amazon_item = self.collection_a.find_one({'Title': {'$regex': search_key, '$options': 'i'}})
            
            if amazon_item:
                logging.info(f"Documento de Amazon recuperado: {amazon_item}")
                amazon_title = amazon_item.get('Title', 'Título no disponible')
                amazon_used_price_str = amazon_item.get('Buy Box Used: 180 days avg.', 0)
                logging.info(f"Valor extraído de 'Buy Box Used: 180 days avg': {amazon_used_price_str}")
                amazon_used_price = self.convert_price(amazon_used_price_str)
                fba_fee_str = amazon_item.get('FBA Fees', 0)
                fba_fee = self.convert_price(fba_fee_str)
                logging.debug(f"Precio de venta en Amazon (Buy Box Used): {amazon_used_price}")
                logging.debug(f"FBA Fees: {fba_fee}")

                referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
                referral_fee = round(amazon_used_price * referral_fee_percentage, 2)
                logging.debug(f"Tarifa de referencia calculada: {referral_fee}")

                total_cost = round(ebay_price + fba_fee + referral_fee, 2)
                profit = round(amazon_used_price - total_cost, 2)
                roi = round((profit / total_cost) * 100, 2) if total_cost else 0
                
                logging.info(f"Precio de venta en Amazon (Buy Box Used): {amazon_used_price}")
                logging.info(f"Tarifa de FBA: {fba_fee}")
                logging.info(f"Tarifa de referencia: {referral_fee}")
                logging.info(f"Ganancia: {profit}")
                logging.info(f"ROI: {roi}%")
                logging.debug(f"Total cost: {total_cost}")
                logging.debug(f"Profit: {profit}")
                logging.debug(f"ROI: {roi}%")

                if roi > 50:
                    current_date = datetime.utcnow()
                    cached_item = self.collection_cache.find_one({
                        'item_number': item.get('item_number'),
                        'expiry_date': {'$gt': current_date}
                    })
                    if cached_item:
                        logging.info(f"Item already exists in cache and is not expired: {item['item_number']}")
                    else:
                        item['last_checked'] = datetime.utcnow()
                        item['_id'] = ObjectId()
                        item['expiry_date'] = current_date + timedelta(days=7)
                        self.collection_cache.insert_one(item)
                        self.send_email(
                            item,
                            item['image_url'],
                            item['product_url'],
                            ebay_price,
                            amazon_item.get('Image', ''),
                            amazon_item.get('URL: Amazon', ''),
                            amazon_used_price,
                            roi,
                            amazon_title
                        )
            else:
                logging.warning(f"No se encontró un artículo de Amazon correspondiente para search_key: {search_key}")
        except Exception as e:
            logging.error(f"Error calculating ROI and sending email: {e}")
            logging.debug(f"Detalles del error: {e}")
            logging.debug(f"Item: {item}")

    def send_email(self, item, ebay_image, ebay_url, ebay_price, amazon_image, amazon_url, amazon_price, roi, amazon_title):
        while True:
            try:
                account = self.gmail_accounts[self.current_account]
                self.current_account = (self.current_account + 1) % len(self.gmail_accounts)
                sender_email = account["email"]
                password = account["password"]
                receiver_email = "xavialerts@gmail.com"
                message = MIMEMultipart("alternative")
                message["Subject"] = amazon_title
                message["From"] = sender_email
                message["To"] = receiver_email
                text = f"""
                Alerta de ROI superior al 50%:
                - Imagen de eBay: {ebay_image}
                - URL de eBay: {ebay_url}
                - Precio de eBay: £{ebay_price:.2f}
                - Imagen de Amazon: {amazon_image}
                - URL de Amazon: {amazon_url}
                - Precio de Amazon: £{amazon_price:.2f}
                - ROI: {roi:.2f}%
                - Página del producto de eBay: {ebay_url}
                """
                html = f"""
                <html>
                <body>
                <h1>Alerta de ROI superior al 50%</h1>
                <p><strong>Imagen de eBay:</strong> <img src="{ebay_image}" /></p>
                <p><strong>URL de eBay:</strong> <a href="{ebay_url}">{ebay_url}</a></p>
                <p><strong>Precio de eBay:</strong> £{ebay_price:.2f}</p>
                <p><strong>Imagen de Amazon:</strong> <img src="{amazon_image}" /></p>
                <p><strong>URL de Amazon:</strong> <a href="{amazon_url}">{amazon_url}</a></p>
                <p><strong>Precio de Amazon:</strong> £{amazon_price:.2f}</p>
                <p><strong>ROI:</strong> {roi:.2f}%</p>
                <p><strong>Página del producto de eBay:</strong> <a href="{ebay_url}">{ebay_url}</a></p>
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
                logging.info("Email sent successfully")
                break
            except smtplib.SMTPException as e:
                logging.error(f"SMTP error occurred: {e}")
                break
