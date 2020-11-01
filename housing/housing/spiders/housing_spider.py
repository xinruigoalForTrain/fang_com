from scrapy import Spider,Request
from scrapy.utils.project import get_project_settings
from scrapy.utils.request import request_fingerprint
from redis import Redis
from ..items import HousingItem
from ..items import DepartmentItem
from pyquery import PyQuery as pq
import re
import time
from scrapy_redis.spiders import RedisSpider
import logging
import socket
import traceback

class HoudsingSpider(RedisSpider):
    name = 'fang_spider'
    # allowed_domains = ['fang.com']

    def __init__(self):
        port = '6379'
        hostname = socket.gethostname()
        host_info = socket.gethostbyname(hostname)
        if host_info.startswith('172'):
            port = '6380'
        settings_map = get_project_settings()
        redis_url = settings_map.get('REDIS_URL')
        host = re.search(r'(\d+.){3}\d+',redis_url).group()
        self.redis = Redis(host=host,port=port)
        self.base_url = 'https://{city}.newhouse.fang.com{suffix}'
        self.url_recorder = open('request_url_record.txt', 'r+', encoding='UTF-8')

    def start_requests(self):
        rest_url_dict = self.check_failed_requests()     # 暂时只能在第二次爬取前调用（但仍然可以实现爬取失败url全覆盖）
        for rest_url in rest_url_dict.keys():
            self.redis.sadd('fang_spider:start_urls', rest_url)
            callback_func = rest_url_dict[rest_url]
            yield Request(rest_url, callback=callback_func, method='GET')
        # city_list = ['wuhan', 'gz', 'cs', 'xz', 'nb']
        # city_list = ['xlglm','leiyang']
        # city_list = ['qiannan','chenzhou']
        city_list = ['wz','changchun']     # 调试用
        # city_list = ['jiamusi','danzhou']
        index_url_list = []
        for city in city_list:
            index_url = self.base_url.format(city=city,suffix='/house/s/')
            print(f"keys in redis:{self.redis.keys('*')},index_url is:{index_url}")
            self.redis.sadd('fang_spider:start_urls',index_url)
            print(f"add urls:{self.redis.smembers('fang_spider:start_urls')}")
            yield Request(index_url,callback=self.parse_district,method='GET',meta={'city':city})
        logging.info(f"********************all start_urls in Redis:{self.redis.smembers('fang_spider:start_urls')}")
        # redis_key = 'room_spider:start_urls'

    def parse_district(self, response):
        try:
            if 'city' in response.meta:
                city = response.meta['city']
            else:
                url_city = response.request.url
                pattern_city = 'https://(\w+).newhouse.fang.com/house/s/$'
                city = re.search(pattern_city,url_city).group(1)
            page_str = response.text
            page_pq = pq(page_str)
            city_mark = page_pq('.tf.f12 a').eq(0).text()
            city_name = re.search('(.*)房产',city_mark).group(1)
            districts = page_pq('#quyu_name a')
            for district_ele in districts.items():
                district = district_ele.text()
                if district == '不限':
                    continue
                district_suffix = district_ele.attr('href')
                district_url = self.base_url.format(city=city,suffix=district_suffix)
                yield Request(district_url,callback=self.parse_department_list,method='GET',meta={'city':city_name,'district':district})
        except Exception as ex:
            logging.error(f"{response.request.url} parse_district have failed")
            logging.error(traceback.format_exc())
            self.record_error(response.request.url)
            # time.sleep(4.45)

    def parse_department_list(self,response):
        page_str = response.text
        page_pq = pq(page_str)
        try:
            if ('city' in response.meta) and ('district' in response.meta):
                city = response.meta['city']
                district = response.meta['district']
            else:
                city = None
                district = None     # 在这个阶段不是特别重要，没有可以不传
            departments = page_pq('.nlc_img')
            # 该区域没有房产信息，则不进入循环
            for department in departments.items():
                department_link = department('a').attr('href')
                department_url = "https:" + department_link
                yield Request(department_url,callback=self.parse_department_detail,method='GET',meta={'city':city,'district':district})
            # 如果存在下一页，进行翻页爬取
            page_bar = page_pq('.page')
            if page_bar:
                url_origin = response.request.url
                page_bar_class = page_bar('a:last').attr('class')
                if page_bar_class != 'active':     # 判断是否到达尾页
                    request_next_page_suffix = page_bar('.next').attr('href')
                    request_next_page_url = re.sub('(https://\S+.fang.com)\S+',fr'\1{request_next_page_suffix}',url_origin)
                    yield Request(request_next_page_url,callback=self.parse_department_list,method='GET',meta={'city':city,'district':district})
        except Exception as ex:
            logging.error(f"{response.request.url} parse_list have failed")
            logging.error(traceback.format_exc())
            self.record_error(response.request.url)
        # time.sleep(8.9)

    def parse_department_detail(self,response):
        try:
            if ('city' in response.meta) and ('city' in response.meta) and (response.meta['city'] is not None) and (response.meta['district'] is not None):
                city = response.meta['city']
                district = response.meta['district']
            else:
                page_pq = pq(response.text)
                navigates = page_pq('.br_left a')
                city = re.search('(.*)新房', navigates[1].text).group(1)
                district = re.search('(.*)楼盘', navigates[2].text).group(1)
            page_str = response.text
            more_links = re.search(r'<a .*?href=".*?".*?>更多详细信息(&gt;|>){1,2}</a>',page_str,re.M)     # 存在多种页面结构,使用正则得到楼盘详细信息(注:大于号需要转义)
            pq_a = pq(more_links[0])
            more_link = pq_a.attr('href')
            request_url = response.request.url
            department_prefix = re.search('https://(.*?).newhouse.fang.com/',request_url)     # 如果正则到，则采用地区+newhouse+补充链接拼接新地址,否则使用在新地址前加协议即可
            if department_prefix:
                more_url = department_prefix.group() + 'house/' + more_link
            else:
                more_url = 'https:' + more_link
            yield Request(more_url,callback=self.parse_department_more,method='GET',meta={'city':city,'district':district})
        except Exception as ex:
            logging.error(f"{response.request.url} parse_detail have failed")
            logging.error(traceback.format_exc())
            self.record_error(response.request.url)

        # time.sleep(8.9)
        # page_pq = pq(page_str)
        # if page_pq('.information_li.mb10 a'):
        #     more_link = page_pq('.information_li.mb10 a').attr('href')
        #     more_url = "https:" + more_link
        # elif page_pq('.more-info a'):
        #     more_link = page_pq('.more-info a').attr('href')
        #     more_url = 'https:' + more_link
        # elif page_pq('.more-info'):
        #     more_link = page_pq('.more-info').attr('href')
        #     more_url = 'https:' + more_link

    def parse_department_more(self, response):
        try:
            page_str = response.text
            page_pq = pq(page_str,parser='html')
            if ('city' in response.meta) and ('district' in response.meta):
                city = response.meta['city']
                district = response.meta['district']
            else:
                navigates = page_pq('.topcrumbs a')
                city = re.search('(.*)新房',navigates[1].text).group(1)
                district = re.search('(.*)楼盘',navigates[2].text).group(1)
            department_item = DepartmentItem()
            department_item['obj'] = 'department'
            department_item['department_name'] = page_pq('h1 a').text().strip()
            alias_field = page_pq('.h1_label').text().strip()
            alias = ''
            if alias_field:
                alias = re.search('别名：(.*)',alias_field).group(1)
            department_item['alias'] = alias
            price_text = page_pq('.main-info-price').text().strip()
            if re.search('\d+(.\d+)?',price_text,re.M):
                department_item['avg_price'] = float(re.search('\d+(.\d+)?',price_text,re.M).group())
            else:
                department_item['avg_price'] = 0.0     # 待售
            department_info = page_pq('.main-item').eq(0)

            info_list = department_info('.list-right')
            department_item['estate_type'] = info_list[0].text.strip()
            ele_labels = info_list('.tag')
            labels = []
            for ele_label in ele_labels.items():
                label = ele_label.text()
                labels.append(label)
            if labels is []:
                department_item['special_property'] = '暂无'
            else:
                department_item['special_property'] = ','.join(labels)
            department_item['build_type'] = department_info('.build_type').text().strip().replace(" ",',')
            department_item['decorate_status'] = info_list[3].text.strip()
            department_item['developer'] = department_info('.list-right-text:eq(0) a').text().strip()
            department_item['address'] = info_list('.list-right-text:eq(1)').text().strip()
            department_item['city'] = city
            department_item['district'] = district
            department_url = response.request.url
            department_desc = re.match(r'https://(\S+).fang.com/(\S+/)?house/(\d+)/housedetail.htm',department_url).group(1)
            department_code = re.match(r'https://(\S+).fang.com/(\S+/)?house/(\d+)/housedetail.htm',department_url).group(3)
            department_item['department_code'] = department_code
            department_item['department_url'] = department_url
            yield department_item
            # 判断主力户型是否存在，存在则继续爬取，否则返回item存入数据库
            room_model = page_pq('#orginalNaviBox')
            the_category = room_model('a:eq(3)')
            if the_category.text() == '户型':
                # 如果存在户型，直接调用获得所有户型的ajax
                room_model_url = f'https://{department_desc}.fang.com/house/ajaxrequest/householdlist_get.php?newcode={department_code}&count=false&room=all&city={city}'
                # 存在主力户型，则取出链接，继续爬取
                # room_model_link = the_category.attr('href')
                # room_model_url = 'https:' + room_model_link
                yield Request(room_model_url,callback=self.save_room_model,method='GET',meta={'department_code':department_code})
                # time.sleep(4.45)
        except Exception as ex:
            logging.error(f"{response.request.url} parse_department_more have failed")
            logging.error(traceback.format_exc())
            self.record_error(response.request.url)

    def save_room_model(self,response):     # 直接请求该楼盘的户型详情
        try:
            if 'department_code' in response.meta:
                department_code = response.meta['department_code']
            else:
                url_housing = response.request.url
                department_code = re.match('https://(\S+).fang.com/house/ajaxrequest/householdlist_get.php\?newcode=(\d+)&\S+',url_housing).group(2)
            room_model_data = response.json()
            for data_row in room_model_data:
                housing_item = HousingItem()
                housing_item['obj'] = 'housing'
                housing_item['sale_status'] = data_row['status']
                housing_item['room'] = data_row['room']
                housing_item['hall'] = data_row['hall']
                housing_item['toilet'] = data_row['toilet']
                housing_item['kitchen'] = data_row['kitchen']
                housing_item['room_model_desc'] = data_row['hx_desp']
                housing_item['room_model_feature'] = data_row['huxing_feature']
                house_img_pic_small = data_row['houseimageurl']
                new_scale = f'{data_row["pic_length"]}x{data_row["pic_width"]}'
                if new_scale == '0x0':
                    housing_item['room_pic_src'] = house_img_pic_small
                else:
                    house_img_pic_big = 'https:' + re.sub('\d+x\d+',new_scale,house_img_pic_small)
                    housing_item['room_pic_src'] = house_img_pic_big
                housing_item['build_area'] = data_row['buildingarea']
                housing_item['inside_area'] = data_row['livingarea']
                reference_price_text = data_row['reference_price']
                if re.search('\d+',reference_price_text):
                    reference_price_num = re.search('\d+',reference_price_text).group()
                    housing_item['reference_price'] = float(reference_price_num)
                else:
                    housing_item['reference_price'] = 0.0
                housing_item['department_code'] = department_code
                yield housing_item
        except Exception as ex:
            logging.error(f"{response.request.url} save_model have failed")
            logging.error(traceback.format_exc())
            self.record_error(response.request.url)

    def check_failed_requests(self):
        url_info = self.url_recorder.readline()
        url_dict = {}
        while url_info:
            match_res = re.match('^={5}crawl url:(https://\S+)\s(\w+)={5}$',url_info)
            if not match_res:
                print(f"warning!! :{url_info} break the format")
            else:
                url = match_res.group(1)
                status = match_res.group(2)
                if (status == 'begin') or (status == 'failed'):
                    url_dict[url] = status
                elif status == 'done':
                    try:
                        url_dict.pop(url)
                    except Exception as ex:
                        print(f'{url} have requested already')
            url_info = self.url_recorder.readline()
        print(f"{len(url_dict.keys())} urls have been interrupt last time,crawl them again")
        pattern_city = 'https://(\S+).newhouse.fang.com/house/s/$'
        pattern_district = 'https://(\S+).newhouse.fang.com/house/s/(\w+)/(b\d+)*'
        pattern_page = 'https://(\S+).fang.com/$'
        pattern_detail = 'https://(\S+).fang.com/house/(\d+)/housedetail.htm'
        pattern_housing = 'https://(\S+).fang.com/house/ajaxrequest/householdlist_get.php\?newcode=(\d+)&\S+'
        rest_url_dict = {}
        for url in url_dict.keys():
            # 根据request正则分类，分发给不同的回调函数，并在dupefilter中删除对应的指纹
            if re.match(pattern_city,url):
                callback_func = self.parse_district
                # self.parse_district(resp)
            elif re.match(pattern_district,url):
                callback_func = self.parse_department_list
                # self.parse_department_list(resp)
            elif re.match(pattern_page,url):
                callback_func = self.parse_department_detail
                # self.parse_department_detail(resp)
            elif re.match(pattern_detail,url):
                callback_func = self.parse_department_more
                # self.parse_department_more(resp)
            elif re.match(pattern_housing,url):
                callback_func = self.save_room_model
                # self.save_room_model(resp)
            else:
                print(f"{url} does match any pattern,check whether it is valid.")
                continue
            rest_url_dict[url] = callback_func
            fp = request_fingerprint(Request(url,callback=callback_func,method='GET'), include_headers=None)
            self.redis.srem(HoudsingSpider.name+':dupefilter',fp)     # 如果dupefilter中不存在将会被忽略，不会报错
            # 将文件中的链接处理完成后，立即清空文件，防止后面写入造成污染
        self.url_recorder.seek(0)     # 回到文件首部
        self.url_recorder.truncate()
        return rest_url_dict

    def parse(self, response):
        print('Anything need to do after crawl job have done?')

    def record_error(self,error_url):
        # 解析返回失败，将记录记入重新爬取列表
        self.url_recorder.write(f'=====crawl url:{error_url} failed=====\n')
        self.url_recorder.flush()

    def close(self, spider, reason):
        # 关闭文件（redis连接要关吗）
        print('some obj close here,such as connection,files……spider')
        self.url_recorder.close()
        self.redis.close()
