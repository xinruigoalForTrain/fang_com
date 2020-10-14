# Scrapy settings for housing project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'housing'

SPIDER_MODULES = ['housing.spiders']
NEWSPIDER_MODULE = 'housing.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'housing (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

DOWNLOAD_FAIL_ON_DATALOSS = True

RETRY_ENABLED = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

DEPTH_PRIORITY = -1

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 4.45
RANDOMIZE_DOWNLOAD_DELAY = True

# DOWNLOAD_TIMEOUT = 25     # 超时设置，不一定都有正向效果

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 3

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'housing.middlewares.HousingSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'housing.middlewares.HousingDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'housing.extensions.RedisSpiderSmartIdleClosedExensions': 500,     # 不知为何没起作用
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'housing.pipelines.HousingPipeline': 300,
   # 'scrapy_redis.pipelines.RedisPipeline':300
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# MYEXT_ENABLED = True

# 配置空闲持续时间单位为 100个 ，一个时间单位为5s
IDLE_NUMBER = 100

# 使用的哈希函数数，默认为6
BLOOMFILTER_HASH_NUMBER = 6

# Bloomfilter使用的Redis内存位，30表示2 ^ 30 = 128MB，默认为22 (1MB 可去重130W URL)
BLOOMFILTER_BIT = 22


# log config
LOG_LEVEL = 'INFO'
LOG_FILE = './housing_crawl_tmp.log'

# Enables scheduling storing requests queue in redis.
SCHEDULER = 'scrapy_redis.scheduler.Scheduler'

REDIS_URL = 'redis://192.168.0.163:6379'
# REDIS_URL = 'redis://192.168.1.115:6379'
# REDIS_URL = 'redis://10.12.222.208:6379'

# Ensure all spiders share same duplicates filter through redis.
DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'


SCHEDULER_PERSIST = True

# more than one start_urls
REDIS_START_URLS_KEY = 'fang_spider:start_urls'
REDIS_START_URLS_AS_SET = True
