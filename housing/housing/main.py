from scrapy.cmdline import execute
import sys
import os
# import spiders.housing_spider as spider
import requests
import re
from pyquery import PyQuery as pq
import time
import socket
import MySQLdb as db

def spider_test(url):
    header = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    resp = requests.get(url,headers=header)
    page_text_origin = resp.text
    page_encoding = resp.encoding
    page_byte = page_text_origin.encode(page_encoding)
    page_text_trans = page_byte.decode('GBK')
    page_pq = pq(page_text_trans,parser='html')
    alias_field = page_pq('.h1_label').text().strip()
    alias = ''
    if alias_field:
        alias = re.search('别名：(.*)', alias_field).group(1)
    print(f'别名：{alias}')
    # page_pq = pq(page_text_origin,parser='html')
    department_info = page_pq('.main-item:eq(0)')
    # special_prop = department_info('.tag')
    # print(special_prop)
    # department_info = page_pq('.main-item:eq(0)')     # 会取出所有节点
    # department_info = page_pq('.main-item:eq(1)')     # 能精准取到第二个子节点
    info_list = department_info.find('.list-right')
    estate_type = info_list[0].text.strip()
    developer = department_info.find('.list-right-text:eq(0) a').text()
    address = department_info.find('.list-right-text:eq(1)').text()
    decorate = info_list[3].text.strip()
    print(f"开发商：{developer},地址：{address},装修:{decorate},物业类型:{estate_type}")
    # print(department_info)
    # print(info_list('.list-right:eq(2)').text())
    for i,info in enumerate(info_list.items()):
        print(f'{i} =====next===== {i}')
        print(info.text())

    # avg_price = 0.0
    # if re.search('\d+(.\d+)?',price_text,re.M):
    #     price_num = re.search('\d+(.\d+)?',price_text).group()
    #     avg_price = float(price_num)
    # print(avg_price)

def collect_room_model_data(url):
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    resp = requests.get(url, headers=header)
    room_models_data = resp.json()
    for room_model_data in room_models_data:
        d = room_model_data
        print(f'户型:{d["room"]}室{d["hall"]}厅{d["toilet"]}卫{d["kitchen"]}厨,参考价格{d["reference_price"]},'
              f'户型特点:{d["huxing_feature"]},建筑面积{d["buildingarea"]},套内面积{d["livingarea"]}')
        housing_img_pic_small = d['houseimageurl']
        new_scale = f'{d["pic_length"]}x{d["pic_width"]}'
        print(new_scale)
        house_img_pic_big = 'https:' + re.sub('\d+x\d+', new_scale, housing_img_pic_small)
        print(house_img_pic_big)
        print("========================next house========================")
    print(len(room_models_data))

def recover_domain(url):
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    resp = requests.get(url, headers=header)
    request_url = resp.request.url
    print(request_url)
    encoding = resp.encoding
    department_prefix = re.search('https://(.*?).newhouse.fang.com/', request_url)
    page_str_origin = resp.text
    resp_b = page_str_origin.encode(encoding)
    page_str = resp_b.decode('GBK')
    more_links = re.findall(r'<a .*?href=".*?".*?>更多详细信息&gt;&gt;</a>', page_str, re.M)
    pq_a = pq(more_links[0])
    more_link = pq_a.attr('href')
    if department_prefix:
        more_url = department_prefix.group() + 'house/' + more_link
    else:
        more_url = 'https:' + more_link
    print(more_url)

def check_department_untouch(department_url_list):
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36'}
    for i,department_url in enumerate(department_url_list):
        print("crawling")
        resp = requests.get(department_url, headers=header)
        encoding = resp.encoding
        page_origin = resp.text
        page_b = page_origin.encode(encoding)
        page_text = page_b.decode('GBK')
        page_pq = pq(page_text)
        department_name = page_pq('h1 a').text().strip()
        case_prop = 'Bad'
        if i % 2 == 0:
            case_prop = 'Good'
        print(f"Status: {case_prop},楼盘：{department_name}，响应时间：{resp.elapsed}")
        time.sleep(4.45)

def proxy_test(proxy_api):
    resp = requests.get(proxy_api)
    resp_json = resp.json()
    proxy_list = resp_json['data']
    for proxy in proxy_list:
        print(f"{proxy['ip']}:{proxy['port']},过期时间：{proxy['expire_time']}")

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    execute(['scrapy','crawl','fang_spider'])
    # proxy_cnf = open(r'../housing/proxy_api.txt', 'r', encoding='utf-8')
    # api_list = proxy_cnf.readlines()
    # API_FIRST = api_list[0]
    # API_NEXT = api_list[1]
    # print(f"API_first:{API_FIRST},api_next{API_NEXT}")
    # spider_test('https://weilansiji.fang.com/house/2820145028/housedetail.htm')
    # collect_room_model_data('https://mzhdyjbd.fang.com/house/ajaxrequest/householdlist_get.php?newcode=2816118140&count=false&room=all&city=%E6%A2%85%E5%B7%9E')
    # recover_domain('https://jinganlangc.fang.com/')
    # recover_domain('https://chuxiong.newhouse.fang.com/house/3420258272.htm')
    # untouch_department = ['https://chuxiong.newhouse.fang.com/house/3420258272/housedetail.htm',
    #                       'https://luomouyizhai.fang.com/house/3419945404/housedetail.htm',
    #                       'https://yirenguzhen0871.fang.com/house/3420060824/housedetail.htm',
    #                       'https://xintiandiym.fang.com/house/3419945394/housedetail.htm',
    #                       'https://zgyzwhdgy.fang.com/house/3419945406/housedetail.htm',
    #                       'https://yangguangshuianwk.fang.com/house/3420060820/housedetail.htm',
    #                       'https://shijijiayuanlf.fang.com/house/3420060816/housedetail.htm',
    #                       'https://huayuanmeijun.fang.com/house/3419196208/housedetail.htm'
    #                       'https://yuanmoubiguiyuan.fang.com/house/3419196216/housedetail.htm',
    #                       'https://jinlanbandao0871.fang.com/house/3420060822/housedetail.htm',
    #                       'https://qicaijiayuancx.fang.com/house/3420268460/housedetail.htm'
    #                       'https://ygsahtwhcyy.fang.com/house/3420060818/housedetail.htm']
    # check_department_untouch(untouch_department)
    # proxy_test('http://api.wandoudl.com/api/ip?app_key=838158bebe091897d592f9768a452a6a&pack=0&num=5&xy=2&type=2&lb=\r\n&mr=2&')
    # host_name = socket.gethostname()
    # addr = socket.gethostbyname_ex(host_name)
    # container_mysql_ip = addr[2][1]
    # connection = db.connect(host="10.12.217.9",port=3309,user='root',passwd='XinRuiGOAL!895',db='crawl_learning',charset='utf8')
    # cursor = connection.cursor()
    # sql = 'select city,count(1) from department group by city'
    # # sql = 'show tables;'
    # res = cursor.execute(sql)
    # data_row = cursor.fetchall()
    # for data in data_row:
    #     print(f"output:{data}")
    # cursor.close()
    # connection.close()



