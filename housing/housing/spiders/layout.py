import scrapy


class LayoutSpider(scrapy.Spider):
    name = 'layout'
    allowed_domains = ['fang.com']
    start_urls = ['http://fang.com/']

    def parse(self, response):
        pass
