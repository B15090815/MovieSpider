# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 21:50:19 2018

@author: 陈仁祥
"""
from bs4 import BeautifulSoup
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = (
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36"
)
# 不加载图片
# dcap["phantomjs.page.settings.loadImages"] = False

# 设置开启Flash功能
pres = {"profile.default_content_setting_values.plugins":1,
"profile.content_settings.plugin_whitelist.adobe-flash-player":1,
"profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player":1,
"PluginsAllowedForUrls":"https://qzone.qq.com/"}

chrome_options = Options()

chrome_options.add_experimental_option("prefs",pres)
# 开启无图形界面模式
# chrome_options.add_argument("--headless")
driver = webdriver.Chrome(chrome_options=chrome_options)

qq = '2303918638'
pwd = 'crx0819'
# qq = '940909580'
# pwd = 'dy3344crx0819'
driver.get("https://qzone.qq.com/")
driver.implicitly_wait(20)
driver.switch_to.frame('login_frame')
driver.find_element_by_id('switcher_plogin').click()
driver.find_element_by_id('u').clear()
time.sleep(3)
driver.find_element_by_id('u').send_keys(qq)
time.sleep(3)
driver.find_element_by_id('p').clear()
driver.find_element_by_id('p').send_keys(pwd)
time.sleep(2)
driver.find_element_by_id('login_button').click()

print("login success")
# driver.implicitly_wait(50)
time.sleep(10)
# 点击发说说的框体
driver.find_element_by_id('QM_Mood_Poster_Inner').click()

driver.implicitly_wait(40)
# 点击说说输入框，进入输入状态
try:
    driver.find_element_by_id('$1_substitutor_content').click()
except Exception as e:
    pass

driver.implicitly_wait(40)
content = driver.find_element_by_id('$1_content_content')
content.clear()
content.send_keys("你好\r\n,世界")

# 激活图片上传框体
time.sleep(4)
a = driver.find_element_by_xpath("//div[@class='attach']/div[1]/a[1]")
chain = ActionChains(driver)
chain.move_to_element(a).perform()
time.sleep(4)
#flag = False
#try:
#    li = driver.find_element_by_xpath("//ul[@class='list']/li[1]")
#    flag = True
#except:
#    pass

#time.sleep(2)
#li.click()
#a = driver.find_element_by_xpath("//div[@class='attach']/")

try:
    w = driver.find_element_by_id("qz_app_imageReader_1")
    w.send_keys("E:\\1.jpg")
except:
    print("fail to open...")

flag = False
try:
    driver.find_element_by_id("verify_dialog_frame")
    flag = True
except:
    pass
img = ""
if flag:
    try:
        driver.switch_to_frame("verify_dialog_frame")
        img = driver.find_element_by_id("verifyImg").get_attribute("src")
        print(img)
    except:
        print("fail get verifyCode")
    finally:
        driver.switch_to_default_content()

# if not (img == ""):
#     headers = {
#         "User-Agent":
#         "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36"
#     }

#     r = requests.get(img, headers=headers)
#     with open("./v.jpg", "wb") as f:
#         f.write(r.content)
time.sleep(15)
d = driver.find_element_by_xpath("//div[@class='op']/a[2]")
d.click()

time.sleep(10)
driver.quit()
# print("ok")
#
#time.sleep(5)
#driver.quit()


#driver.switch_to_frame("verify_dialog_frame")
#img = driver.find_element_by_id("verifyImg")
#img.get_attribute("src")
#driver.switch_to_default_content()

#li = driver.find_element_by_xpath("//ul[@class='list']/li[1]/a")
#chain = ActionChains(driver)
#chain.move_to_element(a).perform()
#a = driver.find_element_by_xpath("//div[@class='attach']/div[1]/a[1]")
