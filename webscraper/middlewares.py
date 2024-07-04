import random
from scrapy import signals

class WebscraperSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WebscraperDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def __init__(self):
        self.proxies = [
            'http://xavi1:RgEPGXAbDFgPC5o@proxy.packetstream.io:31112',
            'http://xavi2:oVBm8bOHzQWpunj@proxy.packetstream.io:31112',
            'http://xavi3:voxmQNnV0AyB51y@proxy.packetstream.io:31112',
            'http://xavi4:1Bmki2NpYY78rKl@proxy.packetstream.io:31112',
            'http://xavi5:4zeI4FunnoJg066@proxy.packetstream.io:31112',
            'http://xavi6:azwKgkph6HNK2V8@proxy.packetstream.io:31112',
            'http://xavi7:hSGN0SMxdVgtrwI@proxy.packetstream.io:31112',
            'http://xavi8:DDObyMivD20g3Ai@proxy.packetstream.io:31112',
            'http://xavi9:XN19G5qHiMPlNXf@proxy.packetstream.io:31112',
            'http://xavi10:8WBDburqlbadn1U@proxy.packetstream.io:31112'
        ]

    def process_request(self, request, spider):
        proxy = random.choice(self.proxies)
        request.meta['proxy'] = proxy
        spider.logger.info(f'Using proxy: {proxy}')
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
