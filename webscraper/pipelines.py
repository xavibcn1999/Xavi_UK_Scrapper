import pymongo
from scrapy.exceptions import DropItem
import logging

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
            mongo_collection=crawler.settings.get('MONGODB_COLLECTION', 'Search_uk_E')
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
                upsert=False  # Ensure it does not create a new document
            )
            logging.info(f"Item updated in MongoDB: {item}")
            return item
        except Exception as e:
            logging.error(f"Failed to update item in MongoDB: {e}")
            raise e
