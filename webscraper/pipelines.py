# pipelines.py
import pymongo
from scrapy.exceptions import DropItem

class MongoDBPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection = self.db['Search_uk_E']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.collection.update_one(
            {'ASIN': item['ASIN']},
            {'$set': {
                'image_url': item['Image_URL'],
                'product_title': item['Product_Title'],
                'product_price': item['Product_Price'],
                'shipping_fee': item['Shipping_Fee']
            }},
            upsert=True
        )
        return item
