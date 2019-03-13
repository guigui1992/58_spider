# -*- coding:utf-8 -*-
import re
import base64
import io
from fontTools.ttLib import TTFont
from bs4 import BeautifulSoup
import time
import pymysql.cursors
import requests

## 由于现在的58对一些数字增加密文（我2018年初爬的时候还没有)，导致爬下来数字乱码，增加了解密的操作。
def convert_font(url):
    # proxies=get_random_ip(ipList)
    # ua=UserAgent()
    # headers={'User-Agent':ua.random}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'Cookie': 'id58=c5/njVpymhR0X0thDRuHAg==; commontopbar_new_city_info=79%7C%E6%9D%AD%E5%B7%9E%7Chz; 58tj_uuid=763a5398-da95-4db2-9a54-ba7f4171f17c; new_uv=1; wmda_uuid=80797b44db9604b45dfbf4807417e58f; wmda_new_uuid=1; wmda_visited_projects=%3B2385390625025; commontopbar_ipcity=hz%7C%E6%9D%AD%E5%B7%9E%7C0; commontopbar_myfeet_tooltip=end; als=0; xxzl_deviceid=d7wGUAUqik8MomhIMsEH98iyUnHRBDyrCJYsasv1uq9biXZ%2F%2Bxav%2BhZr%2FQQmLjYF; wmda_session_id_2385390625025=1517477544470-6db397e1-9d59-3e58'
        # 'Host': 'cdata.58.com',
        # 'Referer': 'http://webim.58.com/index?p=rb'
    }
    resp = requests.get(url, headers=headers)
    if resp:
        base64_str = re.findall('data:application/font-ttf;charset=utf-8;base64,(.*)\'\) format\(\'truetype\'\)}',
                                resp.text)
        print(base64_str)
        bin_data = base64.b64decode(base64_str[0])
        fonts = TTFont(io.BytesIO(bin_data))
        bestcmap = fonts.getBestCmap()
        newmap = {}
        for key in bestcmap.keys():
            print(key)
            print(re.findall(r'(\d+)', bestcmap[key]))
            value = int(re.findall(r'(\d+)', bestcmap[key])[0]) - 1
            key = hex(key)
            newmap[key] = value

        print('==========', newmap)
        resp_ = resp.text
        for key, value in newmap.items():
            key_ = key.replace('0x', '&#x') + ';'
            if key_ in resp_:
                resp_ = resp_.replace(key_, str(value))
        return resp_


def getcontent():
    for i in range(1, 71):
        print('----爬到第%d----' % (i))
        url = 'http://hz.58.com/chuzu/pn%s?utm_source=sem-sales-baidu-pc&spm=57652269916.14911347018&utm_campaign=sell&utm_medium=cpc' % str(
            i)
        # proxies=get_random_ip(ipList)
        # ua=UserAgent()
        # headers={'User-Agent':ua.random}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Cookie': 'id58=c5/njVpymhR0X0thDRuHAg==; commontopbar_new_city_info=79%7C%E6%9D%AD%E5%B7%9E%7Chz; 58tj_uuid=763a5398-da95-4db2-9a54-ba7f4171f17c; new_uv=1; wmda_uuid=80797b44db9604b45dfbf4807417e58f; wmda_new_uuid=1; wmda_visited_projects=%3B2385390625025; commontopbar_ipcity=hz%7C%E6%9D%AD%E5%B7%9E%7C0; commontopbar_myfeet_tooltip=end; als=0; xxzl_deviceid=d7wGUAUqik8MomhIMsEH98iyUnHRBDyrCJYsasv1uq9biXZ%2F%2Bxav%2BhZr%2FQQmLjYF; wmda_session_id_2385390625025=1517477544470-6db397e1-9d59-3e58'
            # 'Host': 'cdata.58.com',
            # 'Referer': 'http://webim.58.com/index?p=rb'
        }
        # driver=requests.get(url, headers=headers)
        text = convert_font(url)
        soup = BeautifulSoup(text, 'lxml')
        # print (soup)
        # print(soup.select("li.apartments"))
        for info in soup.select("li.apartments"):

            rent_info = []
            if info.select("div.des") == []:
                continue

            des = info.select("div.des")[0]
            # print (des)
            # 标题
            Item['title'] = des.select("h2")[0].get_text()

            # 房型
            Item['room_type'] = des.select("p.room")[0].get_text().split(';')[0]
            # 面积
            Item['area'] = des.select("p.room")[0].get_text().split(';')[-1]
            add = []
            for one_add in des.select("p.add"):
                add.append(one_add.get_text())
            # print(add)
            add = ';'.join(add)
            Item['address'] = add
            Item['department'] = ''
            if des.select("p.gongyu") != []:
                # 房源类型
                Item['rent_origin_type'] = des.select("p.gongyu > span")[0].get_text()
                # 房源
                Item['rent_origin'] = des.select("p.gongyu")[0].get_text()
            elif des.select("p.geren") != []:
                Item['rent_origin_type'] = des.select("p.geren > span")[0].get_text()
                Item['rent_origin'] = ''
            else:

                # 房源类型
                Item['rent_origin_type'] = des.select("div.jjr")[0].get_text()
                # 房源
                Item['rent_origin'] = des.select("span.jjr_par_dp")[0].get_text()
                # 发布时间
            listliright = info.select("div.listliright")[0]
            Item['send_time'] = listliright.select("div.sendTime")[0].get_text()
            # 价格
            Item['price'] = listliright.select("div.money")[0].select("b")[0].get_text()
            # sql="insert into hz_58_rent_information ('rent_type','room_type','room_area','town','department','address','rent_origin_type','rent_origin_team','send_time','price') \
            # values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"
            cursor.execute('insert into hz_58_rent_information values("%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (
            Item['title'], Item['room_type'], Item['area'], Item['address'], Item['department'],
            Item['rent_origin_type'], Item['rent_origin'], Item['send_time'], Item['price']))
            db.commit()
        for info in soup.select("li[logr]"):
            rent_info = []

            if info.select("div.des") == []:
                continue

            des = info.select("div.des")[0]
            # print (des)
            # 标题
            Item['title'] = des.select("h2")[0].get_text()
            # print (Item['title'])
            # 房型
            Item['room_type'] = des.select("p.room")[0].get_text().split(';')[0]
            # 面积
            Item['area'] = des.select("p.room")[0].get_text().split(';')[-1]
            add = []
            for one_add in des.select("p.add > a"):
                add.append(one_add.get_text())

            add = ';'.join(add)
            Item['address'] = add
            Item['department'] = ''
            if des.select("p.gongyu") != []:
                # 房源类型
                Item['rent_origin_type'] = des.select("p.gongyu > span")[0].get_text()
                # 房源
                Item['rent_origin'] = des.select("p.gongyu")[0].get_text()
            elif des.select("p.geren") != []:
                Item['rent_origin_type'] = des.select("p.geren > span")[0].get_text()
                Item['rent_origin'] = ''
            else:

                # 房源类型
                if des.select("div.jjr") != []:
                    Item['rent_origin_type'] = '来自经纪人'
                # 房源
                if des.select("span.jjr_par_dp") == []:
                    Item['rent_origin'] = ''
                else:
                    Item['rent_origin'] = des.select("span.jjr_par_dp")[0].get_text()
                # 发布时间
            listliright = info.select("div.listliright")[0]
            Item['send_time'] = listliright.select("div.sendTime")[0].get_text()
            # 价格
            Item['price'] = listliright.select("div.money")[0].select("b")[0].get_text()

            # print (Item['title'])
            # print (Item['area'])
            # sql="insert into hz_58_rent_information ('rent_type','room_type','room_area','town','department','address','rent_origin_type','rent_origin_team','send_time','price') \
            # values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"
            cursor.execute(
                'insert into hz_58_rent_information_2019 values("%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (
                Item['title'], Item['room_type'], Item['area'], Item['address'], Item['department'],
                Item['rent_origin_type'], Item['rent_origin'], Item['send_time'], Item['price']))
            db.commit()

        time.sleep(20)


if __name__ == "__main__":
    # ipList=get_ip_list()
    Item = {}

    db = pymysql.connect("localhost", "root", '123456', 'spider', charset='utf8')
    cursor = db.cursor()

    getcontent()