# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 13:16:42 2018

@author:crx
"""
import __init__
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
from Util import mail, IPpool_thread
from Util.setting import rootLogger
# import IPpool_thread, mail
# from setting import rootLogger


class Url(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.urlList = []

    def get(self):
        self.lock.acquire()
        if not self.empty():
            url = self.urlList.pop()
        else:
            url = None
        self.lock.release()
        return url

    def put(self, url):
        self.urlList.append(url)

    def empty(self):
        return len(self.urlList) < 1

    def size(self):
        return len(self.urlList)


class Ipset():
    """
    ip is a list:[ipAddr, True]
    ipAddr is ip address
    Ture is or not useful
    """
    def __init__(self,ip):
        self.ipset = ip
        self.lock = threading.RLock()

    def empty(self):
        return len(self.ipset) < 1

    def getip(self):
        self.lock.acquire()
        if self.empty():
            ip = None
        else:
            ip = random.choice(self.ipset)
            self.ipset.remove(ip)
        self.lock.release()
        return ip

    def releaseip(self,ip):
        self.ipset.append(ip)

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
    def __init__(self, url, siteName, SqlConnection,parseIndex,parsePage,NumThread=4,cy=5):
        self.url = url
        self.connection = SqlConnection
        self.parseIndex = parseIndex
        self.parsePage = parsePage
        self.NumThread = NumThread
        self.cycle = cy
        self.MailMsg = '<h2>{site}</h2>'.format(site=siteName)
        self.signal = threading.Event()
        self.condition = threading.Lock()
        self.resultlist = []
        self.firstlink = Url()

    def download(self, url, proxy, user_agent):
        if proxy is None:
            return None
        proxies = {'http':'http://'+proxy,'https':'https://'+proxy}
        headers = {'User-Agent': user_agent}
        try:
            r = requests.get(url, headers=headers,proxies=proxies,timeout=2)
            if r.status_code == 200:
                if len(r.text) > 100:
                    r.encoding = chardet.detect(r.content)['encoding']
                    return r.text
                else:
                    return None
        except Exception:
            return None


    def getpagelinks(self):
        global User_agent_list,ipset
        cycle = self.cycle
        while cycle > 0:
            proxy = ipset.getip()
            userAgent = random.choice(User_agent_list)
            html = self.download(self.url,proxy,userAgent)
            ipset.releaseip(proxy)
            if html is None:
                cycle -= 1
                time.sleep(2)
            else:
                soup = BeautifulSoup(html,'lxml')
                self.parseIndex(soup,self.firstlink)
                break

    def getsource(self):
        while True:
            # rootLogger.error("getsource working...")
            self.condition.acquire()
            if self.firstlink.empty():
                self.NumThread = self.NumThread - 1
                self.condition.release()
                break
            self.condition.release()

            url = self.firstlink.get()
            cycle = self.cycle
            while cycle > 0:
                proxy = ipset.getip()
                userAgent = random.choice(User_agent_list)
                html = self.download(url, proxy, userAgent)
                ipset.releaseip(proxy)
                if html is None:
                    cycle -= 1
                    time.sleep(2)
                else:
                    soup = BeautifulSoup(html, 'lxml')
                    self.parsePage(soup, self.resultlist)
                    break

        rootLogger.critical(threading.current_thread().getName() + " exited")

    def output(self):
        global datasize
        cursor = self.connection.cursor()
        UpdateNum = 0
        item_id = 0
        NewSourceDate = time.strftime("%Y-%m-%d")
        time.sleep(6)
        while True:
            # rootLogger.error(threading.current_thread().getName()+" output working...")
            while len(self.resultlist) > 0:
                # rootLogger.error(" output working...")
                item = self.resultlist.pop()
                item_id = 0
                if item[4]:
                    # pass
                    # 检测该影视条目是否存在，若存在则判断资源链接数目是否大于
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
                            Inc = LinkSize - LinkNum
                            item[3] = item[3][0:Inc]
                            UpdateNum = Inc + LinkNum
                            UpdateNum = "更新至第" +str(UpdateNum) + "集"


                if len(item[3]) > 0:
                    try:
                        if item_id == 0:
                            cursor.execute(
                                'insert into movie_items(name,img,tag,pubdate) values (%s,%s,%s,%s)',
                                (item[0], item[1], item[2], NewSourceDate))
                            id = cursor.lastrowid
                            UpdateNum = "有" + str(len(item[3])) + "条下载链接"
                        else:
                            id = item_id
                        info = [tuple([each, id]) for each in item[3]]
                        cursor.executemany('insert into movie_links(link,item_id) values (%s,%s)',info)
                        self.connection.commit()
                        datasize += 1
                        self.MailMsg = self.MailMsg + "<h4>{name}</h4><p>{series}</p><img src={href}>".format(
                            name=item[0], series=UpdateNum, href=item[1])
                    except Exception as e:
                        self.connection.rollback()
                        rootLogger.error(str(e))

            if self.NumThread == 0:
                break
            else:
                time.sleep(2)

        self.signal.set()
        # rootLogger.critical(threading.current_thread().getName() + " exited")
        # rootLogger.critical(threading.current_thread().getName()+" working result:" + str(len(self.resultlist)) + " Numthread:"+str(self.NumThread)+" qsize:"+str(self.firstlink.qsize()))

    def sendEmai(self):
        self.signal.wait()
        NewSourceDate = time.strftime("%Y-%m-%d")
        subject = NewSourceDate + " 电影更新情况"
        self.MailMsg += "<h1>今日更新{datasize}条数据</h1>".format(datasize=datasize)
        mail.mail(self.MailMsg, subject=subject)

    def run(self):
        self.getpagelinks()
        if self.firstlink.empty():
            self.signal.set()
            self.MailMsg = self.MailMsg + "<p>今天还没有资源更新</p>"
            self.sendEmai()
            return
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
    testUrl = 'http://www.dy2018.com'
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
    fp_user = open('../Util/user_agent.bi', 'rb')
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

    datasize = 0
    # 电影天堂
    url = 'http://www.dy2018.com'
    siteName = '电影天堂'
    Dy2018 = Update(url, siteName, conn, dy2018Com.parseIndex, dy2018Com.parsePage)
    Dy2018.run()
