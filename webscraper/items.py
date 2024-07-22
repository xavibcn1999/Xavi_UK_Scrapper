import scrapy

class WebscraperItem(scrapy.Item):
    ASIN = scrapy.Field()
    Image_URL = scrapy.Field()
    Product_Title = scrapy.Field()
    Product_Price = scrapy.Field()
    Shipping_Fee = scrapy.Field()
