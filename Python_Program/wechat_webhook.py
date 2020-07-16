#import http.client
import json
import urllib
import requests
import sys
import datetime
webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=？？？？"
#添加企业微信机器人webhook地址



def wechatwork_robot(primaryEmail,familyName,givenName,ad_password,mail_password,orgUnitPath,PhoneNumber):
	now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	headers = {"Content-Type": "text/plain"}
	data = {
		"msgtype": "markdown",
		"markdown": {
		"content": '''**<font color=\"info\">【新员工账号开通提醒】</font>**\n新员工姓名：%s \n邮箱：%s \n域账号密码：%s \n邮箱密码：%s \n电话号码：%s \nOU路径：%s \n '''%(familyName+givenName,primaryEmail,ad_password,mail_password,PhoneNumber,orgUnitPath)
			}
		}
	r = requests.post(url=webhook_url,headers=headers, json=data)
	print(r.text)


