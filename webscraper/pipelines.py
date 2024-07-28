import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient
from bson import ObjectId  # Asegúrate de importar ObjectId
import logging
from datetime import datetime

class MongoDBPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.mongo_uri = settings.get('MONGO_URI')
        self.mongo_db = settings.get('MONGO_DATABASE')
        self.collection_name_e = settings.get('MONGO_COLLECTION_E')
        self.collection_name_a = settings.get('MONGO_COLLECTION_A')
        self.collection_name_cache = 'Search_uk_Cache'  # New collection for caching
        self.gmail_accounts = [
            {"email": "xavusiness@gmail.com", "password": "tnthxazpsezagjdc"},
            {"email": "xaviergomezvidal@gmail.com", "password": "cqpbqwvqbqvjpmly"},
            {"email": "xavigv77@gmail.com", "password": "crdgantmezylfjyq"},
            {"email": "xavigv0408@gmail.com", "password": "excohgpjkrbyvbtn"},
            {"email": "xavigomezvidal@gmail.com", "password": "lunuwnctjjsbchzx"},
            {"email": "xavibcn1999@gmail.com", "password": "vcjlpcfemckrpsvm"}
        ]
        self.current_account = 0
        self.exchange_rate = 1.29  # 1 GBP = 1.29 USD

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_e = self.db[self.collection_name_e]
        self.collection_a = self.db[self.collection_name_a]
        self.collection_cache = self.db[self.collection_name_cache]  # Connect to the new collection

    def close_spider(self, spider):
        self.clean_cache()
        self.client.close()

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

        # Ensure item_number and product_url are in item and not empty
        item['item_number'] = item.get('item_number', '')
        item['product_url'] = item.get('product_url', '')

        # Update item in the Search_uk_E collection
        self.collection_e.update_one({'_id': item['_id']}, {'$set': item}, upsert=True)

        # Add item number to the Search_uk_E collection
        self.collection_e.update_one({'_id': item['_id']}, {'$set': {'item_number': item.get('item_number')}}, upsert=True)

        # Calculate and potentially send email
        self.calculate_and_send_email(item)

        return item

    def convert_price(self, price_str):
        if isinstance(price_str, str):
            price_str = price_str.replace('£', '').replace('US $', '').replace('+', '').replace(',', '').strip()
            if 'US' in price_str:
                return float(price_str) / self.exchange_rate
        return float(price_str)

    def calculate_and_send_email(self, item):
        try:
            ref_number = item['reference_number']
            ebay_price = round(item['product_price'] + item['shipping_fee'], 2)
            logging.info(f"Calculando ROI para número de referencia: {ref_number}")
            logging.info(f"Precio del producto en eBay: {item['product_price']}")
            logging.info(f"Costo de envío en eBay: {item['shipping_fee']}")
            logging.info(f"Precio de eBay (producto + envío): {ebay_price}")

            amazon_item = self.collection_a.find_one({'ReferenceNumber': ref_number})
            if amazon_item:
                logging.info(f"Documento de Amazon recuperado: {amazon_item}")

                amazon_title = amazon_item.get('Title', 'Título no disponible')
                amazon_used_price_str = amazon_item.get('Buy Box Used: 180 days avg.', 0)
                logging.info(f"Valor extraído de 'Buy Box Used: 180 days avg': {amazon_used_price_str}")

                if isinstance(amazon_used_price_str, str):
                    try:
                        amazon_used_price = self.convert_price(amazon_used_price_str)
                    except ValueError as e:
                        logging.error(f"Error al convertir 'Buy Box Used: 180 days avg' a float: {e}")
                        amazon_used_price = 0.0
                else:
                    amazon_used_price = float(amazon_used_price_str)

                fba_fee_str = amazon_item.get('FBA Fees', 0)
                if isinstance(fba_fee_str, str):
                    try:
                        fba_fee = self.convert_price(fba_fee_str)
                    except ValueError as e:
                        logging.error(f"Error al convertir 'FBA Fees' a float: {e}")
                        fba_fee = 0.0
                else:
                    fba_fee = float(fba_fee_str)

                referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
                referral_fee = round(amazon_used_price * referral_fee_percentage, 2)

                total_cost = round(ebay_price + fba_fee + referral_fee, 2)
                profit = round(amazon_used_price - total_cost, 2)
                roi = round((profit / total_cost) * 100, 2) if total_cost else 0

                logging.info(f"Precio de venta en Amazon (Buy Box Used): {amazon_used_price}")
                logging.info(f"Tarifa de FBA: {fba_fee}")
                logging.info(f"Tarifa de referencia: {referral_fee}")
                logging.info(f"Ganancia: {profit}")
                logging.info(f"ROI: {roi}%")

                ebay_url = item['product_url']

                if roi > 50:
                    # Check cache before sending email
                    current_date = datetime.utcnow()
                    cached_item = self.collection_cache.find_one({
                        'item_number': item.get('item_number'),
                        'expiry_date': {'$gt': current_date}
                    })
                    if cached_item:
                        logging.info(f"Item already exists in cache and is not expired: {item['item_number']}")
                    else:
                        item['last_checked'] = datetime.utcnow()
                        item['_id'] = ObjectId()  # Ensure a new _id is generated for the cache
                        item['expiry_date'] = current_date + timedelta(days=7)  # Set expiry date to 7 days from now
                        self.collection_cache.insert_one(item)
                        self.send_email(
                            item,  # Passing item to send_email method
                            item['image_url'], ebay_url, ebay_price,
                            amazon_item.get('Image', ''), amazon_item.get('URL: Amazon', ''), amazon_used_price, roi, amazon_title
                        )
        except Exception as e:
            logging.error(f"Error calculating ROI y sending email: {e}")

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

                text = f"""\
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
                html = f"""\
                <html>
              
              <body>
                <h4>{amazon_title}</h4>
                <p><strong>Precio de Amazon:</strong> £{amazon_price:.2f}</p>
                <p><strong>Precio de eBay:</strong> £{ebay_price:.2f}</p>
                <p style="font-size: 1.5em;"><strong>ROI:</strong> {roi:.2f}%</p>
                <p><strong>Página del producto de eBay:</strong> <a href="{item['product_url']}" target="_blank">URL del producto</a></p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <a href="{ebay_url}" target="_blank">
                    <img src="{ebay_image}" width="250" height="375" alt="eBay Image">
                  </a>
                  <a href="{amazon_url}" target="_blank">
                    <img src="{amazon_image}" width="250" height="375" alt="Amazon Image">
                  </a>
                </div>
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

                logging.info(f"Email enviado exitosamente desde {sender_email}")

                # Update cache after successful email send
                self.collection_cache.update_one(
                    {'_id': item['_id']},
                    {'$set': item},
                    upsert=True
                )
                break
            except smtplib.SMTPException as e:
                logging.error(f"Error al enviar email con la cuenta {sender_email}: {e}")
                if "Daily user sending limit exceeded" in str(e):
                    logging.info(f"Cambio de cuenta debido al límite diario alcanzado: {sender_email}")
                elif "Username and Password not accepted" in str(e):
                    logging.info(f"Cambio de cuenta debido a credenciales incorrectas: {sender_email}")
                else:
                    break
                self.current_account = (self.current_account + 1) % len(self.gmail_accounts)
