# www.dy2018.com parse rule

import time
import re
import threading
from setting import rootLogger

def parseIndex(soup, firstlink):
    # rootLogger.critical(threading.current_thread().getName() + " parse Index")
    NewSourceDate = time.strftime("%m-%d")
    url = 'http://www.dy2018.com'
    try:
        blocks = soup.find_all('div', class_='co_area2')
        for block in blocks:
            source = block.find('ul').find_all('li')
            for item in source:
                a = item.find('a')
                href = url + a.get('href')
                date = item.find('span').text
                if date == NewSourceDate:
                    firstlink.put(href)
    except Exception as e:
        rootLogger.error(str(e))

def parsePage(soup, resultlist):
    # rootLogger.critical(threading.current_thread().getName() + " parse Index")
    try:
        content = soup.find('div', id='Zoom')
        # logging.error(content)
        img = content.find('img').get('src')
        position = soup.find('div', class_='position')
        tag = ""
        if position:
            a = position.find_all("a")
            for each in a:
                tag = tag + each.text + "_"

        title = soup.find(class_="title_all")
        if title:
            name = title.text
        else:
            name = "NoName"
        td = content.find_all('td')
        link = []
        for item in td:
            a = item.find('a')
            if a:
                link.append(a.get('href'))
        pattern = re.compile(r'连载')
        IsSeries = pattern.search(name)
        pattern = re.compile(r'(?<=《)[^》]*')
        tname = pattern.search(name)
        if tname:
            name = tname.group()
        if bool(IsSeries):
            resultlist.append([name, img, tag, link,True])
        else:
            resultlist.append([name, img, tag, link,False])
    except Exception as e:
        rootLogger.error(str(e))
