# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 13:16:42 2018

@author:crx
"""

import requests
from bs4 import BeautifulSoup
import random
import pickle
import chardet
import time
import threading
import logging
import logging.handlers
import queue
import pymysql
import sys
import time
import dy2018Com

logging.basicConfig(
    level=logging.ERROR,
    format=
    '%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S')

rotateFlieHander = logging.handlers.RotatingFileHandler(filename='update.log', maxBytes=1024, backupCount=1)
logging.root.addHandler(rotateFlieHander)

class Ipset():
    """
    ip is a list:[ipAddr, True]
    ipAddr is ip address
    Ture is or not useful
    """
    def __init__(self,ip):
        self.ipset = [[i, True] for i in ip]
        self.lock = threading.Lock()
        self.size = len(ip)
        self.OriginSize = self.size
        self.index = -1
    def empty(self):
        return self.size < 1

    def getip(self):
        self.lock.acquire()
        if self.empty():
            ip = None
        else:
            self.index = (self.index + 1) % self.OriginSize
            ip = self.ipset[self.index]
            # ip = random.choice(self.ipset)
            while not ip[1]:
                self.index = (self.index + 1) % self.OriginSize
                ip = self.ipset[self.index]
                # ip = random.choice(self.ipset)
            ip[1] = False
            self.size -= 1
        self.lock.release()
        return ip

    def releaseip(self,ip):
        ip[1] = True
        self.size += 1

    def output(self):
        print(self.ipset)

"""
电影天堂
"""
class Update(object):
    """
    cycle:maximun ip tests default 4 times
    function:
        getpagelinks
        getsource [name,img,tag,link]
    """
    def __init__(self, url, siteName, SqlConnection,parseIndex,parsePage,NumThread=4):
        self.url = url
        self.name = siteName
        self.connection = SqlConnection
        self.parseIndex = parseIndex
        self.parsePage = parsePage
        self.NumThread = NumThread
        self.resultlist = []
        self.firstlink = queue.Queue()

    def download(self, url, cycle=5):
        # cycle = cy
        global User_agent_list,ipset
        while cycle > 0:
            ip = ipset.getip()
            if ip is None:
                return None
            proxy = ip[0]
            proxies = {'http':'http://'+proxy,'https':'https://'+proxy}
            headers = {'User-Agent':random.choice(User_agent_list)}
            try:
                r = requests.get(url, headers=headers,proxies=proxies,timeout=2)
                break
            except Exception:
                cycle -= 1
                time.sleep(3)
            finally:
                ipset.releaseip(ip)

        if cycle > 0:
            r.encoding = chardet.detect(r.content)['encoding']
            return r.text
        else:
            logging.error('fail to craw the page url from ' + self.name)
            return None

    def getpagelinks(self):
        html = self.download(self.url)
        if html is None:
            return None
        soup = BeautifulSoup(html,'lxml')
        self.parseIndex(soup,self.firstlink)

    def getsource(self):
        while not self.firstlink.empty():
            html = self.download(self.firstlink.get())
            if html is None:
                return None
            soup = BeautifulSoup(html, 'lxml')
            self.parsePage(soup,self.resultlist)
        self.NumThread -= 1

    def output(self):
        cursor = self.connection.cursor()
        NewSourceDate = time.strftime("%Y-%m-%d")
        while (len(self.resultlist) > 0) or (self.NumThread > 0):
            if len(self.resultlist) > 0:
                item = self.resultlist.pop()
                try:
                    cursor.execute(
                        'insert into movie_items(name,img,tag,pubdate) values (%s,%s,%s,%s)',
                        (item[0], item[1], item[2], NewSourceDate))
                    id = cursor.lastrowid
                    info = [tuple([each, id]) for each in item[3]]
                    cursor.executemany('insert into movie_links(link,item_id) values (%s,%s)',info)
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()
                    logging.error(str(e))
            else:
                time.sleep(2)

    def run(self):
        self.getpagelinks()
        num = self.NumThread
        while num > 0:
            t = threading.Thread(target=self.getsource)
            t.start()
            num -= 1
        s = threading.Thread(target=self.output)
        s.start()

if __name__ == '__main__':
    try:
        # print('connecting mysql...')
        conn = pymysql.connect(host='127.0.0.1',port=3306,user='root',passwd='admin',db='movie',charset='utf8')
        # print("connect mysql success...")
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
    # open UserAgent list
    fp_user = open('./user_agent.bi','rb')
    User_agent_list = pickle.load(fp_user)
    fp_user.close()
    # open IP list
    fp_IP = open("./CrawIP.bi","rb")
    IPpool = pickle.load(fp_IP)
    fp_IP.close()
    ipset = Ipset(IPpool)
    IPpool = None  # release IPpool due to it has used

    # 电影天堂
    url = 'http://www.dy2018.com'
    siteName = '电影天堂'
    Dy2018 = Update(url, siteName, conn, dy2018Com.parseIndex, dy2018Com.parsePage)
    Dy2018.run()
