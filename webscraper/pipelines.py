import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

        self.collection_e.update_one({'_id': item['_id']}, {'$set': item}, upsert=True)
        self.calculate_and_send_email(item)
        return item

    def convert_price(self, price_str):
        if isinstance(price_str, str):
            price_str = price_str.replace('£', '').replace('US $', '').replace('+', '').replace(',', '').strip()
            if 'US' in price_str:
                return float(price_str) / self.exchange_rate
            return float(price_str)
        return float(price_str)

    def calculate_and_send_email(self, item):
        try:
            asin = item['nkw']
            ebay_price = round(item['product_price'] + item['shipping_fee'], 2)
            logging.debug(f"Calculating ROI for ASIN: {asin}")
            logging.debug(f"eBay product price: {item['product_price']}, shipping fee: {item['shipping_fee']}")
            logging.debug(f"Total eBay price: {ebay_price}")

            amazon_item = self.collection_a.find_one({'ASIN': asin})
            if amazon_item:
                logging.debug(f"Amazon item found for ASIN {asin}")
                amazon_title = amazon_item.get('Title', 'Título no disponible')
                amazon_used_price_str = amazon_item.get('Buy Box Used: 180 days avg.', 0)
                logging.debug(f"Value extracted from 'Buy Box Used: 180 days avg': {amazon_used_price_str}")

                if isinstance(amazon_used_price_str, str):
                    try:
                        amazon_used_price = self.convert_price(amazon_used_price_str)
                    except ValueError as e:
                        logging.error(f"Error converting 'Buy Box Used: 180 days avg' to float: {e}")
                        amazon_used_price = 0.0
                else:
                    amazon_used_price = float(amazon_used_price_str)

                fba_fee_str = amazon_item.get('FBA Fees', 0)
                if isinstance(fba_fee_str, str):
                    try:
                        fba_fee = self.convert_price(fba_fee_str)
                    except ValueError as e:
                        logging.error(f"Error converting 'FBA Fees' to float: {e}")
                        fba_fee = 0.0
                else:
                    fba_fee = float(fba_fee_str)

                referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
                referral_fee = round(amazon_used_price * referral_fee_percentage, 2)
                total_cost = round(ebay_price + fba_fee + referral_fee, 2)
                profit = round(amazon_used_price - total_cost, 2)
                roi = round((profit / total_cost) * 100, 2) if total_cost else 0

                logging.debug(f"Amazon used price: {amazon_used_price}")
                logging.debug(f"FBA fee: {fba_fee}")
                logging.debug(f"Referral fee: {referral_fee}")
                logging.debug(f"Total cost: {total_cost}")
                logging.debug(f"Profit: {profit}")
                logging.debug(f"ROI: {roi}%")

                ebay_url = f"https://www.ebay.co.uk/sch/i.html?_from=R40&_trksid=p2334524.m570.l1313&_nkw={asin}&_sacat=267&LH_TitleDesc=0&_odkw=1492086894&_osacat=267&LH_BIN=1&_sop=15&LH_PrefLoc=1&rt=nc&LH_ItemCondition=2750%7C4000%7C5000%7C6000%7C10"

                if roi > 50:
                    logging.info(f"ROI > 50% detected for ASIN {asin}")

                    # Check cache before sending email
                    cached_item = self.collection_cache.find_one({
                        'nkw': item['nkw'],
                        'product_title': item['product_title'],
                        'image_url': item['image_url']
                    })

                    if cached_item:
                        logging.info(f"Item already exists in cache: {item['nkw']} - {item['product_title']}")
                        # Update timestamp to mark as relevant
                        self.collection_cache.update_one(
                            {'_id': cached_item['_id']},
                            {'$set': {'last_checked': datetime.utcnow()}}
                        )
                        logging.debug(f"Cache entry updated for ASIN {asin}")
                    else:
                        logging.info(f"New item to be added to cache: {item['nkw']} - {item['product_title']}")
                        item['last_checked'] = datetime.utcnow()
                        try:
                            result = self.collection_cache.update_one(
                                {'_id': item['_id']},
                                {'$set': item},
                                upsert=True
                            )
                            logging.debug(f"Cache update result: matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id}")
                        except Exception as e:
                            logging.error(f"Error updating cache: {e}")

                        self.send_email(
                            item['image_url'],
                            ebay_url,
                            ebay_price,
                            amazon_item.get('Image', ''),
                            amazon_item.get('URL: Amazon', ''),
                            amazon_used_price,
                            roi,
                            amazon_title
                        )
                        logging.info(f"Email sent for ASIN {asin}")
                else:
                    logging.debug(f"ROI {roi}% is not > 50%, no email sent for ASIN {asin}")
            else:
                logging.warning(f"No Amazon item found for ASIN {asin}")
        except Exception as e:
            logging.exception(f"Error calculating ROI and sending email: {e}")

    def send_email(self, ebay_image, ebay_url, ebay_price, amazon_image, amazon_url, amazon_price, roi, amazon_title):
        try:
            account = self.gmail_accounts[self.current_account]
            self.current_account = (self.current_account + 1) % len(self.gmail_accounts)
            sender_email = account["email"]
            password = account["password"]
            receiver_email = "xavialerts@gmail.com"

            logging.debug(f"Sending email from {sender_email} to {receiver_email}")

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
            """
            html = f"""
            <html>
            <body>
                <p>Alerta de ROI superior al 50%:</p>
                <ul>
                    <li><b>Imagen de eBay:</b> {ebay_image}</li>
                    <li><b>URL de eBay:</b> <a href="{ebay_url}">{ebay_url}</a></li>
                    <li><b>Precio de eBay:</b> £{ebay_price:.2f}</li>
                    <li><b>Imagen de Amazon:</b> {amazon_image}</li>
                    <li><b>URL de Amazon:</b> <a href="{amazon_url}">{amazon_url}</a></li>
                    <li><b>Precio de Amazon:</b> £{amazon_price:.2f}</li>
                    <li><b>ROI:</b> {roi:.2f}%</li>
                </ul>
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

            logging.info(f"Email sent successfully for item: {amazon_title}")
        except Exception as e:
            logging.exception(f"Error sending email: {e}")
            if "Daily user sending limit exceeded" in str(e):
                logging.info(f"Cambio de cuenta debido al límite diario alcanzado: {sender_email}")
                self.current_account = (self.current_account + 1) % len(self.gmail_accounts)
                self.send_email(ebay_image, ebay_url, ebay_price, amazon_image, amazon_url, amazon_price, roi, amazon_title)
            elif "Username and Password not accepted" in str(e):
                logging.info(f"Cambio de cuenta debido a credenciales incorrectas: {sender_email}")
                self.current_account = (self.current_account + 1) % len(self.gmail_accounts)
                self.send_email(ebay_image, ebay_url, ebay_price, amazon_image, amazon_url, amazon_price, roi)
