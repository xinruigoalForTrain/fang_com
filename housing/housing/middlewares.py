# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import NotConfigured
from fake_useragent import UserAgent
from proxy_pool import Proxy_pool
from twisted.internet import defer
from twisted.internet.error import TimeoutError,DNSLookupError,ConnectionRefusedError,ConnectionDone,ConnectError,ConnectionLost,TCPTimedOutError
from twisted.web.client import ResponseFailed
from scrapy.core.downloader.handlers.http11 import TunnelError
import time
import traceback

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


    def __init__(self, idle_number, crawler):
        self.ua = UserAgent()
        self.proxy_util = Proxy_pool()
        self.request_writer = open('request_url_record.txt','a+',encoding='utf-8')     # 需要提交到线上
        self.crawler = crawler
        self.idle_number = idle_number
        self.idle_list = []
        self.idle_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        # s = cls()
        # crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        # return s
        # if not crawler.settings.getbool('MYEXT_ENABLED'):
        #     raise NotConfigured

        # 配置仅仅支持RedisSpider
        # if not 'redis_key' in crawler.spidercls.__dict__.keys():
        #     raise NotConfigured('Only supports RedisSpider')

        # get the number of items from settings

        idle_number = crawler.settings.getint('IDLE_NUMBER', 100)

        # instantiate the extension object

        ext = cls(idle_number, crawler)

        # connect the extension object to signals

        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)

        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        crawler.signals.connect(ext.spider_idle, signal=signals.spider_idle)

        # return the extension object

        return ext

    def process_request(self, request, spider):
        try:
            fake_ua = self.ua.random
            url = request.url
            print(f"=====crawl url:{url} begin=====")
            self.request_writer.write(f'=====crawl url:{url} begin=====\n')
            self.request_writer.flush()
            proxy_kind = url.split(":")[0]
            request.headers['User-Agent'] = fake_ua
            header_tmp = {'user_agent':fake_ua}
            # proxy = self.proxy_util.output_proxy(url,header_tmp)
            proxy = self.proxy_util.output_proxy_from_zm(url,header_tmp)
            print(f"the proxy will be {proxy},kind of proxy is {proxy_kind}")
        except Exception as ex:
            spider.logger.error(traceback.format_exc())
            time.sleep(5)
            self.request_writer.write(f'=====crawl url:{url} begin=====\n')
            self.request_writer.flush()
        # if proxy_kind == 'https':
        #     proxy_str = f"https://{proxy}"
        # elif proxy_kind == 'http':
        #     proxy_str = f"http://{proxy}"
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
                # print(f'request meta contain these items:{request.meta.keys()},type is {type(request.meta.keys()[0])}')
                # print(f'request header contain these items:{request.headers.keys()},type is {type(request.meta.keys()[0])}')
                if 'Cookie'.encode(encoding='utf-8') in request.meta.keys():
                    print("clear Cookie")
                    del request.meta['Cookie']
            except SyntaxError:
                print('error here,do nothing about it')
            return request
        self.request_writer.write(f"=====crawl url:{request.url} done=====\n")
        self.request_writer.flush()
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
                # print(f'request meta contain these items:{request.meta.keys()},type is {type(request.meta.keys()[0])}')
                # print(f'request header contain these items:{request.headers.keys()},type is {type(request.meta.keys()[0])}')
                if 'Cookie'.encode(encoding='utf-8') in request.headers.keys():
                    print("clear Cookie")
                    del request.headers['Cookie']
            except SyntaxError:
                print('error here,do nothing about it')
            return request
        else:
            spider.logger.info(f"other exception {exception}")
            return None
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain

    def spider_opened(self, spider):
        spider.logger.info(f"opened spider {spider.name} redis spider Idle, Continuous idle limit： {self.idle_number}")

    def spider_closed(self, spider):
        self.request_writer.close()
        spider.logger.info(f"closed spider {spider.name},idle count {self.idle_count},Continuous idle count {len(self.idle_list)}")

    def spider_idle(self, spider):
        self.idle_count += 1
        self.idle_list.append(time.time())
        idle_list_len = len(self.idle_list)

        # 判断 redis 中是否存在关键key, 如果key 被用完，则key就会不存在
        if idle_list_len > 2 and spider.server.exists(spider.redis_key):
            self.idle_list = [self.idle_list[-1]]

        elif idle_list_len > self.idle_number:
            spider.logger.info(f"""continued idle number exceed {self.idle_number} Times 
                        meet the idle shutdown conditions, will close the reptile operation 
                        idle start time: {self.idle_list[0]}, close spider time: {self.idle_list[0]}""")
            # 执行关闭爬虫操作
            self.crawler.engine.close_spider(spider, 'closespider_pagecount')

