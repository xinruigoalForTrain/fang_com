# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from fake_useragent import UserAgent
from proxy_pool import Proxy_pool
from twisted.internet import defer
from twisted.internet.error import TimeoutError,DNSLookupError,ConnectionRefusedError,ConnectionDone,ConnectError,ConnectionLost,TCPTimedOutError
from twisted.web.client import ResponseFailed
from scrapy.core.downloader.handlers.http11 import TunnelError
import time
import logging

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class HousingSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class HousingDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    ALL_EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                      ConnectionRefusedError, ConnectionDone, ConnectError,
                      ConnectionLost, TCPTimedOutError, ResponseFailed,
                      IOError, TunnelError)


    def __init__(self):
        self.ua = UserAgent()
        self.proxy_util = Proxy_pool()
        logging.basicConfig(filename='housing_error.log',level=logging.ERROR)


    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        fake_ua = self.ua.random
        url = request.url
        print(f"=====crawl url:{url}=====")
        proxy_kind = url.split(":")[0]
        header_tmp = {'user_agent':fake_ua}
        # proxy = self.proxy_util.output_proxy(url,header_tmp)
        proxy = self.proxy_util.output_proxy_from_zm(url,header_tmp)
        # print(f"the proxy will be {proxy},kind of proxy is {proxy_kind}")
        request.headers['User-Agent'] = fake_ua
        if proxy_kind == 'https':
            proxy_str = f"https://{proxy}"
        elif proxy_kind == 'http':
            proxy_str = f"http://{proxy}"
        request.meta['proxy'] = proxy
        if proxy is None:
            print("use your proxy")
            request.meta['proxy'] = None

    def process_response(self, request, response, spider):
        resp_code = response.status
        if resp_code > 300:
            print(f"{request.url} crawl failed directly,try it again,status code is {resp_code}")
            header_dict = {'user_agent':str(request.headers['User-Agent'], encoding='utf-8')}
            new_proxy = self.proxy_util.output_proxy_from_zm(request.url, header_dict)
            # new_proxy = self.proxy_util.output_proxy_from_zm(request.url, request.headers['User-Agent'])
            print(f"invalid proxy is {request.meta['proxy']},new_proxy is {new_proxy}")
            request.meta['proxy'] = new_proxy
            try:
                print(f'request meta contain these items:{request.meta.keys()},type is {type(request.meta.keys()[0])}')
                print(f'request header contain these items:{request.headers.keys()},type is {type(request.meta.keys()[0])}')
                if 'Cookie'.encode(encoding='utf-8') in request.meta.keys():
                    print("clear Cookie")
                    del request.meta['Cookie']
            except SyntaxError:
                print('error here,do nothing about it')
            return request
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception,self.ALL_EXCEPTIONS):
            print(f"{request.url} download fail,cause:{exception},change the header and proxy then try it again later")
            time.sleep(4.45)
            header_dict = {'user_agent': str(request.headers['User-Agent'], encoding='utf-8')}
            new_proxy = self.proxy_util.output_proxy_from_zm(request.url, header_dict)
            print(f"invalid proxy is {request.meta['proxy']},new_proxy is {new_proxy}")
            request.meta['proxy'] = new_proxy
            try:
                print(f'request meta contain these items:{request.meta.keys()},type is {type(request.meta.keys()[0])}')
                print(f'request header contain these items:{request.headers.keys()},type is {type(request.meta.keys()[0])}')
                if 'Cookie'.encode(encoding='utf-8') in request.headers.keys():
                    print("clear Cookie")
                    del request.headers['Cookie']
            except SyntaxError:
                print('error here,do nothing about it')
            return request
        else:
            logging.error(f"other exception {exception}")
            return None
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
