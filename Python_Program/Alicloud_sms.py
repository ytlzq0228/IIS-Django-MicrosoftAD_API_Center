
#!/usr/bin/env python
#coding=utf-8

import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest


class SMS:

	def sent_sms(to_address,from_sign,TemplateCode,TemplateParam,):
		try:
			client = AcsClient('LTA*******Qqz8WL', '9bCAXA9*******2x0mEvZy', 'ap-southeast-1')
			request = CommonRequest()
			request.set_accept_format('json')
			request.set_domain('dysmsapi.ap-southeast-1.aliyuncs.com')
			request.set_method('POST')
			request.set_version('2018-05-01')
			request.set_action_name('SendMessageWithTemplate')
			request.add_query_param('To', to_address)
			request.add_query_param('From', from_sign)
			request.add_query_param('TemplateCode', TemplateCode)
			request.add_query_param('TemplateParam', TemplateParam)
			response = client.do_action(request)
		except Exception as err:
			raise err
		else:
			return str(response, encoding = 'utf-8')



