# webscraper/pipelines.py

from pymongo import MongoClient

class MongoDBPipeline:

    def open_spider(self, spider):
        try:
            spider.logger.info("Opening MongoDB pipeline...")
            self.client = MongoClient('mongodb+srv://xavidb:superman123@serverlessinstance0.lih2lnk.mongodb.net/')
            self.db = self.client["Xavi_UK"]
            self.collection_E = self.db['Search_uk_E']
            spider.logger.info("MongoDB pipeline opened.")
        except Exception as e:
            spider.logger.error(f"Error connecting to MongoDB in pipeline: {e}")

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            update_result = self.collection_E.update_one(
                {'ASIN': item['ASIN']},
                {'$set': {
                    'Image URL': item['Image URL'],
                    'Product Title': item['Product Title'],
                    'Product Price': item['Product Price'],
                    'Shipping Fee': item['Shipping Fee']
                }},
                upsert=True
            )
            if update_result.modified_count > 0:
                spider.logger.info(f"Data updated for ASIN: {item['ASIN']}")
            elif update_result.upserted_id is not None:
                spider.logger.info(f"New document inserted for ASIN: {item['ASIN']}")
            else:
                spider.logger.warning(f"No document was updated or inserted for ASIN: {item['ASIN']}, the data might be the same.")
        except Exception as e:
            spider.logger.error(f"Error updating MongoDB for ASIN: {item['ASIN']} - {e}")
        return item
