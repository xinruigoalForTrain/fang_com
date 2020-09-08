# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import MySQLdb as db
import time
import items


class HousingPipeline:
    def __init__(self):
        self.connection =db.connect(host="127.0.0.1",user='root',passwd='XinRuiGOAL!895',db='crawl_learning',charset='utf8')
        self.cursor = self.connection.cursor()

    def process_item(self, item, spider):     # 注意查看item的类别
        # print(f"item is {type(item)}, class is:{item.__class__},item is Dept?:{isinstance(item,items.DepartmentItem)}")  #isinstance判断为False
        # print(f"dept is {type(dept)}, class is:{item.__class__},item is Dept?:{isinstance(dept,items.DepartmentItem)}")  #isinstance判断为True
        obj = item["obj"]
        if obj == 'department':
            cur_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())     # str类型，不能在初始化时获取，否则时间会同一变成爬取时间
            sql = f'''insert into department (`city`,`district`,`department_name`,`alias`,`special_property`,
                        `build_type`,`estate_type`,`developer`,`decorate_status`,`address`,`avg_price`,
                        `department_code`,`department_url`,`create_time`,`update_time`) 
                values ('{item["city"]}','{item["district"]}','{item["department_name"]}','{item["alias"]}',
                        '{item["special_property"]}','{item["build_type"]}','{item["estate_type"]}','{item["developer"]}',
                        '{item["decorate_status"]}','{item["address"]}',{item["avg_price"]},{item["department_code"]},
                        '{item["department_url"]}',
                        STR_TO_DATE('{cur_time}',"%Y-%m-%d %H:%i:%s"),STR_TO_DATE('{cur_time}',"%Y-%m-%d %H:%i:%s"))'''
            self.cursor.execute(sql)
            self.connection.commit()
            print(f"保存楼盘：{item['department_name']}，所在城市：{item['city']}")
        elif obj == 'housing':
            cur_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
            sql = f'''insert into housing(`department_id`,`department_code`,`sale_status`,`room`,`hall`,`toilet`,
                    `kitchen`,`room_model_desc`,`room_model_feature`,`room_pic_src`,`build_area`,`inside_area`,
                    `reference_price`,`create_time`,`update_time`) 
                    values(0,{item["department_code"]},'{item["sale_status"]}',{item["room"]},{item["hall"]},
                    {item["toilet"]},{item["kitchen"]},'{item["room_model_desc"]}','{item["room_model_feature"]}',
                    '{item["room_pic_src"]}',{item["build_area"]},{item["inside_area"]},{item["reference_price"]},
                    STR_TO_DATE('{cur_time}',"%Y-%m-%d %H:%i:%s"),STR_TO_DATE('{cur_time}',"%Y-%m-%d %H:%i:%s"))'''
            self.cursor.execute(sql)
            self.connection.commit()

    def close_spider(self,spider):
        # 可在此调用housing的department_id和department的id同步的方法
        self.cursor.close()
        self.connection.close()
        print("connection closed here")