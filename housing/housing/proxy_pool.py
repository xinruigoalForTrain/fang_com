import requests
import re
import time
from pyquery import PyQuery as pq
import random

class Proxy_pool():
    def __init__(self):
        self.proxy_list = []
        self.proxy_time_map = {}
        self.proxy_banned_time = {}
        proxy_output = ""

    def output_proxy(self,url_used,header):
        proxy_output = None
        proxy_pool_size = len(self.proxy_list)
        if proxy_pool_size == 0:
            self.get_proxy_from_89(header, 5)     # 基础款，先提取5个ip，如果未采集到，则扩大容量，直至有ip补充进来
        proxy_picked = self.proxy_list.pop(0)
        print(f"{proxy_picked} out!")
        proxy_checked = self.check_proxy_valid(proxy_picked,url_used,header)
        if proxy_checked is None:
            self.output_proxy(url_used,header)
        else:
            proxy_output = proxy_checked
            self.proxy_list.append(proxy_picked)     # 如果可用，就将IP反充回IP池中
        print(f"{proxy_picked} output!")
        return proxy_output

    def output_proxy_from_zm(self,url_used,header):
        proxy_output = None
        if len(self.proxy_list) == 0:
            try:
                self.get_proxy_from_zm('http://webapi.http.zhimacangku.com/getip?num=20&type=2&pro=0&city=0&yys=0&port=11&pack=115882&ts=1&ys=0&cs=0&lb=1&sb=0&pb=45&mr=2&regions=')     # 初始状态下一次取一定数量的IP
                # time.sleep(4.45)
            except Exception as ex:
                self.get_proxy_from_89(header,5)
                print(ex)
        proxy_pool_size = len(self.proxy_list)
        while proxy_pool_size == 0:
            print('wait for proxy join in…………………………')
            time.sleep(0.89)
        rand_index = random.randint(0, proxy_pool_size-1)
        # if proxy_pool_size < 7:
        #     t_err = time.strftime('%Y-%m-%s %H:%M:%S',time.mktime(time.localtime()))
        #     print(f"Unknown error happens!ip_pool size is:{proxy_pool_size},while index is:{rand_index},err_time:{t_err}")
        #     time.sleep(4.45)
        proxy_picked = self.proxy_list[rand_index]
        print(f'proxy {proxy_picked} have picked')
        proxy_checked = self.check_proxy_valid(proxy_picked, url_used, header)
        if proxy_checked is None:     # 如果代理失效，检查是否过期,是否多次被banned
            banned_times = self.proxy_banned_time[proxy_picked]
            if banned_times > 5:
                self.remove_invalid_proxy_and_filling_new(proxy_picked,header)
            elif proxy_picked in self.proxy_time_map.keys():
                t_expire = time.mktime(time.strptime(self.proxy_time_map[proxy_picked],'%Y-%m-%d %H:%M:%S'))
                t_now = time.mktime(time.localtime())
                if t_now >= t_expire:
                    self.remove_invalid_proxy_and_filling_new(proxy_picked,header)
            self.output_proxy_from_zm(url_used, header)     # 重新从代理池中提取
        else:
            proxy_output = proxy_checked
        print(f"{proxy_picked} output!")
        return proxy_output

    def remove_invalid_proxy_and_filling_new(self,invalid_proxy,header):
        self.proxy_list.remove(invalid_proxy)  # 如果当前时间大于代理过期时间，将此代理删除
        print(f"{invalid_proxy} removed")
        try:
            self.get_proxy_from_zm(
                'http://webapi.http.zhimacangku.com/getip?num=1&type=2&pro=0&city=0&yys=0&port=11&pack=115882&ts=1&ys=0&cs=0&lb=1&sb=0&pb=45&mr=2&regions=')  # 调用API补充进一个代理
        except Exception as e:
            self.get_proxy_from_89(header, 5)     # 如果API失效将暂时从89ip中补充

    def get_proxy_from_89(self, header, n):
        # headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}
        resp = requests.get(
            url=f'http://www.89ip.cn/tqdl.html?num={n}&address=%E4%B8%8A%E6%B5%B7&kill_address=&port=&kill_port=&isp=',
            headers=header)
        if resp.status_code != 200:
            print(f"Warning!! 89ip have problem,response code is:{resp.status_code}")
        proxy_page_text = resp.text
        proxy_page_dom = pq(proxy_page_text)
        proxy_content = proxy_page_dom('h1').siblings('div').text()
        proxies = re.findall('((\d+\.){3}\d+:\d+)', proxy_content,re.S)
        for proxy_item in proxies:
            self.proxy_list.append(proxy_item[0])
            self.proxy_banned_time[proxy_item[0]] = 0
            print(f"加入代理：{proxy_item[0]} from 89")
        if len(self.proxy_list) == 0:
            time.sleep(55)
            n += 1
            print(f"提取IP数量扩大至：{n}")
            self.get_proxy_from_89(header, n)

    def get_proxy_from_zm(self,api):
        resp = requests.get(api)
        result = resp.json()
        if resp.status_code != 200 or (not result['success']):
            raise Exception('代理API已失效！程序将进入休眠，请尽快处理！')
            # time.sleep(5555)     #中断爬取，待IP充值后恢复（未完成）
        else:
            resp_json = resp.json()
            zm_proxy_list = resp_json['data']
            for proxy in zm_proxy_list:
                proxy_str = f"{proxy['ip']}:{proxy['port']}"
                self.proxy_time_map[proxy_str] = proxy['expire_time']
                self.proxy_banned_time[proxy_str] = 0
                self.proxy_list.append(proxy_str)
                print(f"加入代理：{proxy['ip']}:{proxy['port']} from 芝麻,过期时间：{proxy['expire_time']}")

    def check_proxy_valid(self, proxy_str, url_used, header):
        http_kind = url_used.split(':')[0]
        proxy_picked = {f"{http_kind}":f"{http_kind}://{proxy_str}"}
        retry_times = 0
        while retry_times <= 5:
            try:
                resp = requests.get(url_used,proxies=proxy_picked,headers=header,timeout=(5,25))
            except requests.ConnectTimeout as e:
                if retry_times == 5:
                    return None
                else:
                    retry_times += 1
            except requests.exceptions.ProxyError:
                print(f"proxy {proxy_picked} is banned")
                t0 = int(self.proxy_banned_time[proxy_str])
                self.proxy_banned_time[proxy_str] = (t0 + 1)
                return None
            else:     # 在except状态下不走这里（所以会多一个except）
                if resp.status_code < 400:
                    print(f"{proxy_picked} is effective,oh yeah~")
                    return proxy_str
                else:
                    print(f"Err_code:{resp.status_code}")
                    if resp.status_code == 403:
                        print(f"proxy {proxy_picked} is banned")
                        t0 = int(self.proxy_banned_time[proxy_str])
                        self.proxy_banned_time[proxy_str] = (t0 + 1)
                    return None
