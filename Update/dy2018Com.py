# www.dy2018.com parse rule
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
    name = ''
    tag = ''
    td = content.find_all('td')
    link = []
    for item in td:
        a = item.find('a')
        if a:
            link.append(a.get('href'))
    resultlist.append([name, img, tag, link])
