# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24 10:37:20 2017

"""
import pickle
import random
import chardet
import requests
import json
from lxml import etree
import threading
import time
import re
import mail
import sys
import pymysql
import IPpool_thread
import multiprocessing
import logging
import logging.handlers

logging.basicConfig(
    level=logging.DEBUG,
    format=
    '%(threadName)s>>%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S')

rotateFlieHander = logging.handlers.RotatingFileHandler(
    filename='6v.log', maxBytes=1024*1024 * 5, backupCount=5)
logging.root.addHandler(rotateFlieHander)

#下载器
def download(url,proxy,user_agent):
    headers = {'User-Agent':user_agent}
    proxies = {'http':'http://'+proxy,'https':'https://'+proxy}
    try:
        r = requests.get(url,headers=headers,proxies=proxies,timeout=2)
        if r.status_code == 200:
            r.encoding = chardet.detect(r.content)['encoding']
            return r.text
        else:
            return None
    except Exception as e:
        logging.error(str(e))
        return None

#解析拿到链接
def get_new_urls(soup):
    links = soup.xpath("//div[@class='listBox']/ul/li/div[@class='listimg']/a/@href")
    return  links

#解析拿到数据
def get_new_data(soup):
    """
    [title,image,resource]
    """
    new_data = []
    source = soup.xpath("//div[@id='text']")
    if source:
        source = source[0]
    else:
        return None
    img = source.xpath('./p[1]/img/@src')
    href = source.xpath('.//table/tbody/tr/td/a/@href')
    title = soup.xpath('//div[@class="contentinfo"]/h1/a/text()')
    if title:
        title = title[0]
        tit = titlepattern.search(title)
        if tit:
            title = tit.group()
    else:
        title = 'NoBody'
    new_data.append(title)
    if img:
        img = img[0]
    else:
        img = 'Null'
    new_data.append(img)
    if href:
        new_data.append(href)
    else:
        return None
    return new_data

def data_input(data):
    global datas
    if data is None:
        return
    datas.append(data)

def data_save(filename,data):
    filename = filename + '.json'
    with open(filename,'w') as fp:
        json.dump(data,fp=fp,ensure_ascii=True,indent=4)


class Pageurl():
    """
    url is a set()
    """
    def __init__(self,url,lock):
        self.url = url
        self.lock = lock

    def geturl(self):
        self.lock.acquire()
        if self.empty():
            url = None
        else:
            url = self.url.pop()
        self.lock.release()
        return url

    def puturl(self,url):
        self.lock.acquire()
        self.url.add(url)
        self.lock.release()

    def empty(self):
        return len(self.url) < 1

class Movieurl():
    def __init__(self):
        self.url = set()

    def empty(self):
        return len(self.url) < 1

    def geturl(self):
        if self.empty():
            return None
        else:
            return self.url.pop()

    def puturl(self,urls):
        # print(urls)
        self.url = self.url | urls
        # print(self.url)

class Ipset():
    """
    ip is a list
    """
    def __init__(self,ip,lock):
        self.ipset = ip
        self.lock = lock
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

    def putip(self,ip):
        self.ipset.append(ip)


# ipcondition = threading.Condition()

class PageSpider(threading.Thread):
    def __init__(self,name,pageurl,movieurl,ipset,recycle=4):
        threading.Thread.__init__(self)
        self.setName(name)
        self.pageurl = pageurl
        self.ipset = ipset
        self.movieurl = movieurl
        self.recycle = recycle

    def run(self):
        global pagespiders, pagespiderslock
        while True:
            # time.sleep(2)
            url = self.pageurl.geturl()
            if not (url is None):
                icount = 0
                while icount < self.recycle:
                    ip = self.ipset.getip()
                    user_agent = random.choice(User_agent_list)
                    #print(threading.current_thread().name,"num %d try" % (icount+1),url,ip)
                    # print("number %d try" % (icount+1),threading.current_thread().name,url,ip)
                    html = download(url,ip,user_agent)
                    self.ipset.putip(ip)
                    if not (html is None):
                        # print(threading.current_thread().name,"success")
                        soup = etree.HTML(html)
                        murl = get_new_urls(soup)   #murl is a list
                        murl = set(murl)
                        # print(murl)
                        moviecondition.acquire()
                        self.movieurl.puturl(murl)
                        # print(self.movieurl.url)
                        moviecondition.notify_all()
                        moviecondition.release()
                        break
                    else:
                        icount += 1
                        time.sleep(3)

                if icount == self.recycle:
                    pagefail.append(url)

                    # pagefail.append(url)
            else:
                # print(threading.current_thread().name,'exiting...')
                pagespiderslock.acquire()
                pagespiders += 1
                pagespiderslock.release()
                break


class MovieSpider(threading.Thread):
    def __init__(self,name,movieurl,ipset,recycle=4):
        threading.Thread.__init__(self)
        self.setName(name)
        self.movieurl = movieurl
        self.ipset = ipset
        # self.prolist = prolist
        self.recycle = recycle

    def producerIsalive(self):
        global psize,pagespiders
        return psize == pagespiders
        # for each in self.producerIsalive:
        #     if each.is_alive():
        #         # print(each.name,each.is_alive())
        #         return False


    def run(self):
        global ready
        global timepattern
        while True:
            time.sleep(2)
            moviecondition.acquire()
            if self.producerIsalive() and self.movieurl.empty():
                # print(threading.current_thread().name,'exiting...')
                ready += 1
                moviecondition.release()
                break
            while self.movieurl.empty():
                moviecondition.wait()
            url = self.movieurl.geturl()
            moviecondition.release()
            icount = 0
            while icount < self.recycle:
                ip = self.ipset.getip()
                user_agent = random.choice(User_agent_list)
                # print(threading.current_thread().name,"num %d try" % (icount+1),url,ip)
                html = download(url,ip,user_agent)
                self.ipset.putip(ip)
                if not (html is None):
                    # print(threading.current_thread().name,"success")
                    soup = etree.HTML(html)
                    data = get_new_data(soup)
                    if not (data is None):
                        timerecord = timepattern.search(url)
                        if timerecord:
                            tic = timerecord.group()
                        else:
                            tic = '2017-1-1'
                        data.append(tic)
                        # data['time'] = time.mktime(time.strptime(tic,"%Y-%m-%d"))
                        data_input(data)
                    else:
                        crawdatafail.append(url)
                    break
                else:
                    icount += 1
                    time.sleep(3)
                    # moviefail.append(url)
            if icount == self.recycle:
                moviefail.append(url)



class Outdata(threading.Thread):
    def __init__(self,threadsize,sleeptime=2,filename='auto'):
        threading.Thread.__init__(self)
        self.sleeptime = sleeptime
        self.threadsize = threadsize
        self.filename = filename
    def run(self):
        global ready
        global datas
        global moviefail
        global pagefail
        global crawdatafail
        global subject
        global tag
        global cursor
        global datasize
        print('data save starting...')
        while True:
            while len(datas) > 0:
                datasize += 1
                data = datas.pop()
                name = data[0]
                img = data[1]
                href = data[2]
                pubdate = data[3]
                # print('name:'+name,'img:'+img,'href:'+str(href),'pubdate:'+pubdate,'tag:'+str(tag))
                try:
                    cursor.execute(
                        'insert into movie_items(name,img,tag,pubdate) values (%s,%s,%s,%s)',
                        (name,img,tag,pubdate))
                    # conn.commit()
                    id = cursor.lastrowid
                    info = [tuple([each, id]) for each in href]
                    cursor.executemany('insert into movie_links(link,item_id) values (%s,%s)',info)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    logging.error(str(e))



            if ready == self.threadsize:
                tic = time.strftime("%Y-%m-%d-%H-%M", time.localtime())
                # self.filename = self.filename + tic
                # data_save(self.filename+'-'+tic,datas)
                # data_save(self.filename+'-pagefail-'+tic,pagefail)
                conn.close()
                data_save(self.filename+'-moviefail-'+tic,moviefail)
                data_save(self.filename + '-crawdatafail-' + tic, crawdatafail)
                msg = subject + "本次一共爬取" + str(datasize) + '条数据. ' + tic
                mail.mail(msg)
                # fp = open('./message-'+tic,'w')
                # fp.write(msg)
                # fp.close()
                #print("it is done...")
                # print(datas)
                # print(pagefail)
                # print(moviefail)

                break
            else:
                time.sleep(self.sleeptime)


# sys.argv
# 1:index
# 2:pagerange
# 3:subject
# 4:tag
# 5：startpos default 1
# 6:craw new ip y or n default false(n)

"""
movie type:
1:喜剧
2:动作片
3:爱情
4:恐怖
5:科幻
6:战争
7:纪录片
8:故事片
9:动画片
"""

crawip = 'n'
if len(sys.argv) > 6:
    crawip = sys.argv[6]

if crawip.lower() == 'y':
    print('start crawing ip...')
    testurl = 'http://www.6vhao.tv/'
    p = multiprocessing.Process(target=IPpool_thread.Go,args=(testurl,))
    p.start()
    p.join()
    print('ip has crawed...')



try:
    print('connecting mysql...')
    conn = pymysql.connect(host='127.0.0.1',port=3306,user='root',passwd='admin',db='movie',charset='utf8')
    print("connect mysql success...")
except Exception as e:
    logging.error(str(e))
    sys.exit(1)
cursor = conn.cursor()

datasize = 0

timepattern = re.compile(r'\d{4}-\d{1,2}-\d{1,}')
titlepattern = re.compile(r'[^\u3010].*[^\u3011]')

fp_user = open('./user_agent.bi','rb')
User_agent_list = pickle.load(fp_user)
fp_user.close()

fp_IP = open("./CrawIP.bi","rb")
IPpool = pickle.load(fp_IP)
fp_IP.close()

maxlength = len(IPpool)

datas = []
moviefail = []
pagefail = []
crawdatafail = []

moviecondition = threading.Condition()
iplock = threading.Lock()
pagelock = threading.Lock()
pagespiderslock = threading.Lock()

ready = 0
pagespiders = 0


url_root = "http://www.6vhao.tv"
index = sys.argv[1]
all_link = set()

pagerange = int(sys.argv[2])
startpos = 1
if len(sys.argv) > 5:
    startpos = int(sys.argv[5])

for i in range(pagerange): #153
    i = i + startpos
    if i == 1:
        url = url_root + r'/'+ index + r'/'
    else:
        url = url_root + r'/'+index + r'/' + 'index_' + str(i) + '.html'
    all_link.add(url)

pageurl = Pageurl(all_link,pagelock)
movieurl = Movieurl()
ipset = Ipset(IPpool,iplock)

cycle = int(maxlength*0.6)

#prolist = []
psize = int(maxlength * 0.3)
# psize=1
print('starting spiders threads...')
for i in range(psize):
    name = 'pagespider-'+str(i+1)
    p = PageSpider(name, pageurl, movieurl, ipset, cycle)
    p.start()
    #prolist.append(p)


csize = int(maxlength*0.7)
#conlist = []
# csize=1
for i in range(csize):
    name = 'moviespider-'+str(i+1)
    m = MovieSpider(name, movieurl, ipset, cycle)
    m.start()
    #conlist.append(m)

subject = sys.argv[3]
tag = sys.argv[4]


dataoutput = Outdata(csize,2,subject)
dataoutput.start()
