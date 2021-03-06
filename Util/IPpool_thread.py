# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 20:52:38 2017

@author: 陈仁祥
"""
import random
import pickle
import time
import threading
import queue
from datetime import datetime
from lxml import etree
import requests
from setting import rootLogger


ipq = queue.Queue()
useful=[]
global User_agent_list
fp_user = open('../Util/user_agent.bi','rb')
User_agent_list = pickle.load(fp_user)
fp_user.close()

class TestIp(threading.Thread):
    def __init__(self,testurl):
        threading.Thread.__init__(self)
        self.testurl = testurl

    def run(self):
        global ipq
        global User_agent_list
        global useful
        while True:
            if ipq.empty():
                break
            else:
                ip = ipq.get()
                proxies = {'http':'http://'+ip,'https':'https://'+ip}
                headers = {'User-Agent':random.choice(User_agent_list)}
                # print('%s testing' % threading.current_thread().name)
                ipq.task_done()
                try:
                    r = requests.get(self.testurl,headers=headers,proxies=proxies,timeout=2)
                    if r.status_code == 200:
                        useful.append(ip)
                except:
                    pass


def CrawIP():
    global User_agent_list
    url = 'http://www.xicidaili.com/nt/'
    ips = []
    ports = []
    for j in range(2):
        # print("正在获取%d页IP..."%(j+1))
        if j>0:
            url = url + str(j)
        headers = {'User-Agent':random.choice(User_agent_list)}
        r = requests.get(url,headers=headers)
        html = etree.HTML(r.text)
        ips.extend(html.xpath("//td[@class='country' and position()<2]/following-sibling::td[1]/text()"))
        ports.extend(html.xpath("//td[@class='country' and position()<2]/following-sibling::td[2]/text()"))
        time.sleep(5)
    #ip = queue.Queue()
    global ipq
    for i in range(len(ips)):
        ipq.put(ips[i] + ':' + ports[i])
    rootLogger.error('Ips have downloaded...')
    # print('Ips have downloaded...')
    return

def Go(testurl, filename="./CrawIP.bi"):
    CrawIP()
    threads = []
    for i in range(4):
        thread = TestIp(testurl)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    with open(filename, "wb") as fp:
        pickle.dump(useful,fp)
    rootLogger.error('this time has crawed ' + str(len(useful)) + ' IPs')
    # print('this time has crawed ' + str(len(useful)) + ' IPs')


if __name__ == '__main__'  :
    testurl = 'https://www.dy2018.com/'
    Go(testurl)
