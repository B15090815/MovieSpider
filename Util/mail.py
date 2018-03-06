# -*- coding: UTF-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from Util.setting import rootLogger

my_sender='940909850@qq.com'    # 发件人邮箱账号
my_pass = 'wnmejxuizrudbdfa'    # 发件人邮箱密码 wnmejxuizrudbdfa  dy3344crx0819
my_user='18056962858@163.com'   # 收件人邮箱账号，我这边发送给自己

def mail(message, subject="爬虫运行情况"):
    ret=True
    try:
        msg=MIMEMultipart('related')
        msg['From'] = formataddr(["Server",my_sender])     # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To']=formataddr(["Coder",my_user])             # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        # subject = "爬虫运行情况"
        msg['Subject']=Header(subject,'UTF-8')            # 邮件的主题，也可以说是标题

        # mail_msg = '\
        # 	<p>' + subject + '</p>\
        # 	<p>'+ message + '</p>'


        msg.attach(MIMEText(message, 'html', 'UTF-8'))
        # fp = open(path,'rb')
        # msgImage = MIMEImage(fp.read())
        # fp.close()
        # msgImage.add_header('Content-ID', '<image>')
        # msg.attach(msgImage)

        server=smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender,[my_user,],msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception as e:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        rootLogger.error(str(e))
        # print(e)
        ret=False
    return ret


# mail(
#     "<h4>niao</h4><img src=https://img.diannao1.com/d/file/p/2018-02-16/387a59e136eb8d6eac5687c032325154.jpg>"
# )
# mail("hello 163.com")