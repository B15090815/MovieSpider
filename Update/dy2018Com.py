# www.dy2018.com parse rule
import time
import re
def parseIndex(soup, firstlink):
    NewSourceDate = time.strftime("%m-%d")
    url = 'http://www.dy2018.com'
    blocks = soup.find_all('div', class_='co_area2')
    for block in blocks:
        source = block.find('ul').find_all('li')
        for item in source:
            a = item.find('a')
            href = url + a.get('href')
            date = item.find('span').text
            if date == NewSourceDate:
                firstlink.put(href)


def parsePage(soup, resultlist):
    content = soup.find('div', id='Zoom')
    img = content.find('img').get('src')
    position = soup.find(class_='position')
    if position:
        a = position.find_all("a")
        tag = ""
        for each in a:
            tag = tag + each.text + "_"
        else:
            tag = "Notag"

    title = soup.find(class_="title_all")
    # pattern = re.compile(r'(?<=《)[^》]*')
    if title:
        name = title.text
        # name = pattern.search(title.text)
        # if name:
        #     name = name.group()
        # else:
        #     name = title.text
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
    if IsSeries:
        resultlist.append([name, img, tag, link,True])
    else:
        resultlist.append([name, img, tag, link,False])
