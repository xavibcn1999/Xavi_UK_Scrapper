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
            'http://xavi1:rgepgxabdfgpc5o@proxy.packetstream.io:31112',
        'http://xavi2:ovbm8bohzqwpunj@proxy.packetstream.io:31112',
        'http://xavi3:voxmqnnv0ayb51y@proxy.packetstream.io:31112',
        'http://xavi4:1bmki2npyy78rkl@proxy.packetstream.io:31112',
        'http://xavi5:4zei4funnojg066@proxy.packetstream.io:31112',
        'http://xavi6:azwkgkph6hnk2v8@proxy.packetstream.io:31112',
        'http://xavi7:hsgn0smxdvgtrwi@proxy.packetstream.io:31112',
        'http://xavi8:ddobymivd20g3ai@proxy.packetstream.io:31112',
        'http://xavi9:xn19g5qhimplnxf@proxy.packetstream.io:31112',
        'http://xavi10:8wbdburqlbadn1u@proxy.packetstream.io:31112',
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
