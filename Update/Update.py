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
import sys, getopt
import time
import dy2018Com
import IPpool_thread, mail
from setting import rootLogger


class Ipset():
    """
    ip is a list:[ipAddr, True]
    ipAddr is ip address
    Ture is or not useful
    """
    def __init__(self,ip):
        # self.ipset = [[i, True] for i in ip]
        self.ipset = ip
        self.lock = threading.Lock()
        self.size = len(ip)
        # self.OriginSize = self.size
        self.index = -1
    def empty(self):
        return self.size < 1

    def getip(self):
        self.lock.acquire()
        if self.empty():
            ip = None
        else:
            ip = random.choice(self.ipset)
            self.ipset.remove(ip)
            self.size -= 1
        self.lock.release()
        return ip

    def releaseip(self,ip):
        self.ipset.append(ip)
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
        self.IsOver = False
        self.MailMsg = '<h2>{site}</h2>'.format(site=siteName)
        self.resultlist = []
        self.firstlink = queue.Queue()

    def download(self, url, cycle=5):
        # cycle = cy
        global User_agent_list,ipset
        while cycle > 0:
            proxy = ipset.getip()
            if proxy is None:
                return None

            proxies = {'http':'http://'+proxy,'https':'https://'+proxy}
            headers = {'User-Agent':random.choice(User_agent_list)}
            try:
                # rootLogger.critical("downloading "+url)
                # rootLogger.critical(threading.current_thread().getName() + " trying num " + str(6-cycle) + " times via " + proxy)
                r = requests.get(url, headers=headers,proxies=proxies,timeout=2)
                ipset.releaseip(proxy)
                if r.status_code == 200:
                    break
            except Exception:
                cycle -= 1
                time.sleep(2)
                ipset.releaseip(proxy)

        if cycle > 0 and len(r.text) > 100:

            # rootLogger.critical(threading.current_thread().getName() +
            # " downloading via " + proxy)
            r.encoding = chardet.detect(r.content)['encoding']
            return r.text
        else:
            # rootLogger.error('fail to craw the page url from ' + self.name)
            return None

    def getpagelinks(self):
        html = self.download(self.url)
        if html is None:
            return None
        soup = BeautifulSoup(html,'lxml')
        self.parseIndex(soup,self.firstlink)

    def getsource(self):
        while not self.firstlink.empty():
            # rootLogger.critical(threading.current_thread().getName(
            # ) + " still working" + " empty:" + str(self.firstlink.empty()))
            url = self.firstlink.get()
            # rootLogger.critical(
            #     "naw queue size: " + str(self.firstlink.qsize()))
            html = self.download(url)
            if html is None:
                return None
            soup = BeautifulSoup(html, 'lxml')
            self.parsePage(soup,self.resultlist)
        self.NumThread = self.NumThread - 1
        rootLogger.critical(threading.current_thread().getName() + " exited")

    def output(self):
        # global NumOutput
        cursor = self.connection.cursor()
        # sqlLock = threading.Lock()
        NewSourceDate = time.strftime("%Y-%m-%d")
        while (len(self.resultlist) > 0) or (self.NumThread > 0):
            if len(self.resultlist) > 0:
                item = self.resultlist.pop()
                if item[4]:
                    # sqlLock.acquire()
                    ObjNum = cursor.execute(
                        "select id from movie_items where name = '{name}'".
                        format(name=item[0]))
                    if ObjNum > 0:
                        item_id = cursor.fetchone()[0]
                        LinkNum = cursor.execute(
                            "select count(link) from movie_links where item_id={id}".
                            format(id=item_id))
                        if LinkNum > 0:
                            LinkNum = cursor.fetchone()[0]
                            LinkSize = len(item[3])
                            item[3] = item[3][0:(LinkSize-LinkNum)]
                    # sqlLock.release()

                if len(item[3]) > 0:
                    # rootLogger.critical(item[0]+" "+item[1]+" "+item[2]+" " +str(item[3]))
                    try:
                        cursor.execute(
                            'insert into movie_items(name,img,tag,pubdate) values (%s,%s,%s,%s)',
                            (item[0], item[1], item[2], NewSourceDate))
                        id = cursor.lastrowid
                        info = [tuple([each, id]) for each in item[3]]
                        cursor.executemany('insert into movie_links(link,item_id) values (%s,%s)',info)
                        self.connection.commit()
                        self.MailMsg = self.MailMsg + "<h4>{name}</h4><img src={href}>".format(
                            name=item[0], href=item[1])
                    except Exception as e:
                        self.connection.rollback()
                        rootLogger.error(str(e))
            else:
                time.sleep(5)
        # NumOutput = NumOutput - 1
        self.IsOver = True
        rootLogger.critical(threading.current_thread().getName() + " exited")
        # rootLogger.critical(threading.current_thread().getName()+" working result:" + str(len(self.resultlist)) + " Numthread:"+str(self.NumThread)+" qsize:"+str(self.firstlink.qsize()))
    
    def sendEmai(self):
        # global NumOutput
        time.sleep(20)
        # rootLogger.error("NumOutput:" + str(NumOutput))
        while not self.IsOver:
            rootLogger.error("waiting...")
            time.sleep(20)
        rootLogger.error(self.MailMsg)
        NewSourceDate = time.strftime("%Y-%m-%d")
        mail.mail(self.MailMsg,subject=NewSourceDate + " 电影更新情况")

    def run(self):
        self.getpagelinks()
        # rootLogger.critical(str(self.firstlink))
        num = self.NumThread
        while num > 0:
            t = threading.Thread(target=self.getsource)
            t.start()
            num -= 1
        s = threading.Thread(target=self.output)
        s.start()

        m = threading.Thread(target=self.sendEmai)
        m.start()


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hiIu:")
    except getopt.GetoptError:
        sys.exit(2)
    testUrl = 'https://www.baidu.com/'
    for opt, agr in opts:
        if opt == "-i":
            IPpool_thread.Go(testUrl)
        elif opt == "-u":
            testUrl = agr
        elif opt == '-I':
            IPpool_thread.Go(testUrl)
            sys.exit(0)
        elif opt == "-h":
            print("-h useage\n-i for update IP\n-u for testUrl")
            sys.exit()
    try:
        print('connecting mysql...')
        conn = pymysql.connect(host='127.0.0.1',port=3306,user='root',passwd='admin',db='movie',charset='utf8')
        print("connect mysql success...")
    except Exception as e:
        rootLogger.error(str(e))
        sys.exit(1)
    # open UserAgent list
    fp_user = open('./user_agent.bi','rb')
    User_agent_list = pickle.load(fp_user)
    fp_user.close()
    # open IP list
    fp_IP = open("./CrawIP.bi","rb")
    IPpool = pickle.load(fp_IP)
    fp_IP.close()
    if len(IPpool) < 1:
        rootLogger.error("No ips can be used")
        sys.exit(1)
    ipset = Ipset(IPpool)
    IPpool = None  # release IPpool due to it has used

    # NumOutput = 1
    # MailMsg = ''
    # 电影天堂
    url = 'http://www.dy2018.com'
    siteName = '电影天堂'
    Dy2018 = Update(url, siteName, conn, dy2018Com.parseIndex, dy2018Com.parsePage)
    Dy2018.run()

    # print("It's done")
