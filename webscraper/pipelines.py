import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient
import logging

class MongoDBPipeline:
    def __init__(self):
        settings = get_project_settings()
        self.mongo_uri = settings.get('MONGO_URI')
        self.mongo_db = settings.get('MONGO_DATABASE')
        self.collection_name_e = settings.get('MONGO_COLLECTION_E')
        self.collection_name_a = settings.get('MONGO_COLLECTION_A')

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_e = self.db[self.collection_name_e]
        self.collection_a = self.db[self.collection_name_a]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # Convertir los precios a float
        try:
            item['product_price'] = self.convert_price(item['product_price'])
            if item.get('shipping_fee'):
                item['shipping_fee'] = self.convert_price(item['shipping_fee'])
            else:
                item['shipping_fee'] = 0.0
        except Exception as e:
            logging.error(f"Error converting prices: {e}")
            item['product_price'] = 0.0
            item['shipping_fee'] = 0.0

        # Asegurarse de que el item tiene '_id'
        if '_id' not in item:
            logging.error("El item no tiene '_id'")
            return item

        self.collection_e.update_one({'_id': item['_id']}, {'$set': item}, upsert=True)
        self.calculate_and_send_email(item)
        return item

    def convert_price(self, price_str):
        """Convierte un string de precio a float, eliminando cualquier símbolo adicional."""
        if isinstance(price_str, str):
            price_str = price_str.replace('£', '').replace('+', '').replace(',', '').strip()
        return float(price_str)

    def calculate_and_send_email(self, item):
    try:
        asin = item['nkw']
        ebay_price = round(item['product_price'] + item['shipping_fee'], 2)
        logging.info(f"Calculando ROI para ASIN: {asin}")
        logging.info(f"Precio del producto en eBay: {item['product_price']}")
        logging.info(f"Costo de envío en eBay: {item['shipping_fee']}")
        logging.info(f"Precio de eBay (producto + envío): {ebay_price}")

        amazon_item = self.collection_a.find_one({'ASIN': asin})

        if amazon_item:
            logging.info(f"Documento de Amazon recuperado: {amazon_item}")

            amazon_used_price_str = amazon_item.get('Buy Box Used: 180 days avg.', 0)
            logging.info(f"Valor extraído de 'Buy Box Used: 180 days avg': {amazon_used_price_str}")

            # Verificar si el valor es una cadena antes de intentar convertir
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

            # Calcular el costo total
            total_cost = round(ebay_price + fba_fee + referral_fee, 2)

            # Calcular la ganancia
            profit = round(amazon_used_price - total_cost, 2)

            # Calcular el ROI
            roi = round((profit / total_cost) * 100, 2) if total_cost else 0

            logging.info(f"Precio de venta en Amazon (Buy Box Used): {amazon_used_price}")
            logging.info(f"Tarifa de FBA: {fba_fee}")
            logging.info(f"Tarifa de referencia: {referral_fee}")
            logging.info(f"Ganancia: {profit}")
            logging.info(f"ROI: {roi}%")

            # Generar la URL de eBay
            ebay_url = f"https://www.ebay.co.uk/sch/i.html?_from=R40&_trksid=p2334524.m570.l1313&_nkw={asin}&_sacat=267&LH_TitleDesc=0&_odkw=1492086894&_osacat=267&LH_BIN=1&_sop=15&LH_PrefLoc=1&rt=nc&LH_ItemCondition=2750%7C4000%7C5000%7C6000%7C10"

            if roi > 0.5:
                self.send_email(
                    item['image_url'], ebay_url, ebay_price,
                    amazon_item.get('Image', ''), amazon_item.get('URL: Amazon', ''), amazon_used_price, roi
                )

    except Exception as e:
        logging.error(f"Error calculating ROI and sending email: {e}")
