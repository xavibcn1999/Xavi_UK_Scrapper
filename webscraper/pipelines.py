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
        self.collection_e.update_one({'_id': item['doc_id']}, {'$set': item}, upsert=True)
        self.calculate_and_send_email(item)
        return item

    def calculate_and_send_email(self, item):
        try:
            asin = item['nkw']
            ebay_price = float(item['product_price'].replace('£', '').replace(',', '').strip())

            amazon_item = self.collection_a.find_one({'ASIN': asin})
            if amazon_item:
                amazon_used_price = float(amazon_item.get('Buy Box Used: 180 days avg', '0').replace('£', '').replace(',', '').strip())
                fba_fee = float(amazon_item.get('FBA Fees:', '0').replace('£', '').replace(',', '').strip())
                referral_fee_percentage = 0.153 if amazon_used_price > 5 else 0.051
                referral_fee = amazon_used_price * referral_fee_percentage

                profit = ebay_price - amazon_used_price - fba_fee - referral_fee
                roi = profit / ebay_price if ebay_price else -1  # Cambiado 0 por -1

                if roi > 0.5:
                    self.send_email(
                        item['image_url'], item['product_title'], ebay_price,
                        amazon_item.get('Image', ''), amazon_item.get('URL: Amazon', ''), amazon_used_price, roi
                    )

        except Exception as e:
            logging.error(f"Error calculating ROI and sending email: {e}")

    def send_email(self, ebay_image, ebay_url, ebay_price, amazon_image, amazon_url, amazon_price, roi):
        try:
            sender_email = "xavusiness@gmail.com"
            receiver_email = "xavialerts@gmail.com"
           
