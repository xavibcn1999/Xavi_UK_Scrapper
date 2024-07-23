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
        required_fields = ['ASIN', 'image_url', 'product_title', 'product_price', 'shipping_fee']
        
        for field in required_fields:
            if not item.get(field):
                logging.warning(f"Missing {field} in item: {item}")
                raise DropItem(f"Missing {field} in {item}")

        try:
            self.collection.update_one(
                {'ASIN': item['ASIN']},
                {'$set': {
                    'image_url': item['image_url'],
                    'product_title': item['product_title'],
                    'product_price': item['product_price'],
                    'shipping_fee': item['shipping_fee']
                }},
                upsert=True
            )
            logging.info(f"Item saved to MongoDB: {item}")
            return item
        except Exception as e:
            logging.error(f"Failed to save item to MongoDB: {e}")
            raise e

# Optional: Further debugging to check where items are going
class ZytePipeline:
    
    def process_item(self, item, spider):
        # This pipeline simulates Zyte saving for debugging purposes.
        # In a real scenario, you would replace this with actual Zyte logic.
        logging.info(f"Item saved to Zyte: {item}")
        return item

# settings.py

# Add ZytePipeline to the ITEM_PIPELINES for debugging purpose
ITEM_PIPELINES = {
    'webscraper.pipelines.MongoDBPipeline': 300,
    'webscraper.pipelines.ZytePipeline': 800,  # Ensure Zyte pipeline runs later
}
