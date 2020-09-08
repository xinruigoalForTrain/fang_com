# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class DepartmentItem(scrapy.Item):
    obj = scrapy.Field()                 # item类别(由于在pipeline中无法通过isinstance判别item类型,此处临时借用把item类型存入,事后删除)
    city = scrapy.Field()                # 城市
    district = scrapy.Field()            # 区县
    department_name = scrapy.Field()     # 楼盘名称
    alias = scrapy.Field()               # 楼盘别名
    special_property = scrapy.Field()    # 楼盘特色
    build_type = scrapy.Field()          # 建筑类型（塔楼，高层……）
    estate_type = scrapy.Field()         # 物业类型（普通住宅，住宅底商……）
    developer = scrapy.Field()           # 开发商
    decorate_status = scrapy.Field()     # 装修状况
    address = scrapy.Field()             # 地址
    avg_price = scrapy.Field()           # 均价
    department_url = scrapy.Field()      # 楼盘链接
    department_code = scrapy.Field()      # 楼盘编号（用于采集时与户型关联）
    create_time = scrapy.Field()         # 记录时间(录入时存储)
    update_time = scrapy.Field()         # 更新时间(录入，更新时存储)

class HousingItem(scrapy.Item):
    obj = scrapy.Field()                 # item类别
    department_id = scrapy.Field()       # 所在楼盘
    department_code = scrapy.Field()     # 所在楼盘（用于采集时关联）
    sale_status = scrapy.Field()         # 待售，在售，售罄……
    room = scrapy.Field()                # 卧室数量
    hall = scrapy.Field()                # 客厅数量
    toilet = scrapy.Field()              # 卫生间数量
    kitchen = scrapy.Field()             # 厨房数量
    room_model_desc = scrapy.Field()     # 户型描述
    room_model_feature = scrapy.Field()  # 户型特点
    room_pic_src = scrapy.Field()        # 户型图地址
    build_area = scrapy.Field()          # 建筑面积
    inside_area = scrapy.Field()         # 套内面积
    reference_price = scrapy.Field()     # 套间参考价格
    create_time = scrapy.Field()         # 记录时间(录入时存储)
    update_time = scrapy.Field()         # 更新时间(录入，更新时存储)

