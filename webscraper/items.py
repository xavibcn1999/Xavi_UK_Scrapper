import scrapy

class WebscraperItem(scrapy.Item):
    ASIN = scrapy.Field()
    image_url = scrapy.Field()  # Ensure this matches the field name used in the spider
    product_title = scrapy.Field()
    product_price = scrapy.Field()
    shipping_fee = scrapy.Field()

