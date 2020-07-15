import os
import logging
import sys
import hashlib



from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ApiSite.settings import BASE_DIR
from datetime import datetime


IIS_SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(r"%s\Python_Program"%IIS_SITE_DIR)
import API_Add_User
import Alicloud_sms
import Gsuit_api_request


logger = logging.getLogger("sourceDns.webdns.views")




def run_bat():
	try:
		now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
		f = open(IIS_SITE_DIR+"\log\API_run_log.txt",'a')
		f.writelines('\n'+now)
		f.flush()
		f.close()
		run_result = os.system("test.bat >> %s\log\API_run_log.txt"%IIS_SITE_DIR)
		os.system("del test.bat")
	except Exception as err:
		return err
	else:
		return run_result

def save_log(result):
	try:
		now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
		f = open(IIS_SITE_DIR+"\log\API_run_log.txt",'a')
		f.writelines("\n%s:log:%s" %(now,result))
		f.flush()
		f.close()
	except Exception as err:
		return err


class Microsoft_AD:
	#微软AD域相关操作
	def Add_VPN_User_Group(CNname):
	#添加普通VPN用户权限
		try:
			with open("test.bat", "w") as f:
			#以写模式新建文件（文件名test.bat）
				f.write("dsquery user -upn %s@csdn.com | dsmod group \"CN=VPNUser_1,OU=VPN,DC=csdn,DC=com\" -addmbr"%CNname)
				#dsquery转换UPN至CNname，dsmod添加组内用户
			run_result=run_bat()
		except Exception as err:
			return err
		else:
			return run_result
			
	def Add_VPN_bussiness1_Group(CNname):
	#添加databaseVPN用户权限
		try:
			with open("test.bat", "w") as f:
				f.write("dsquery user -upn %s@csdn.com | dsmod group \"CN=bussiness1,OU=VPN,DC=csdn,DC=com\" -addmbr"%CNname)
			run_result=run_bat()
		except Exception as err:
			return err
		else:
			return run_result
			
	def remove_VPN_bussiness1_Group(CNname):
	#删除databaseVPN用户权限
		try:
			with open("test.bat", "w") as f:
				f.write("dsquery user -upn %s@csdn.com | dsmod group \"CN=bussiness1,OU=VPN,DC=csdn,DC=com\" -rmmbr"%CNname)
			run_result=run_bat()
		except Exception as err:
			return err
		else:
			return run_result
			
	def reset_password(CNname,new_password):
	#重置AD域账号密码
		try:
			with open("test.bat", "w") as f:
				f.write("dsquery user ou=shenzhen,DC=csdn,dc=com -upn %s@csdn.com | dsmod user -pwd %s"%(CNname,new_password))
			run_result=run_bat()
		except Exception as err:
			return err
		else:
			return run_result
	
	def add_database_group(CNname,database_group_name):
	#添加database用户组权限
		try:
			with open("test.bat", "w") as f:  # 以写模式新建文件（文件名test.bat）
				f.write("dsquery user -upn %s@csdn.com | dsmod group \"CN=%s,OU=group,DC=csdn,DC=com\" -addmbr" %(CNname,database_group_name))
			run_result=run_bat()
		except Exception as err:
			return err
		else:
			return run_result
		
class Google_Gsuit:
	#Google_Gsuit类相关操作
	def reset_password(email_address,new_password):
	#重置Google邮箱账号密码
		try:
			run_result=Gsuit_api_request.APIrequest.update_user_password(email_address,new_password)
			#邮箱重置密码
			save_log("reset_google_password email_address:%s,new_password:%s"%(email_address,new_password))
		except Exception as err:
			return err
		else:
			return run_result
			
	def suspend_user(email_address):
	#暂停google账户
		try:
			run_result=Gsuit_api_request.APIrequest.suspend_user(email_address)
			run_result=Gsuit_api_request.APIrequest.update_user_group(email_address,'/ZZ-Resignation')
			#暂停账号，移动账号至离职人员群组
			save_log("suspend_user email_address:%s" %(email_address))
		except Exception as err:
			return err
		else:
			return run_result
			
class Add_User_New_employee:
	def add_user(email_address,mail_password,ad_password,family,given,ou,phone):
	#添加新员工账户，同时创建AD域账户和google账户
		try:
			run_result=API_Add_User.main(email_address,mail_password,ad_password,family,given,ou,phone)
			#谷歌账号创建
			save_log("Add_User_New_employee email:%s,mail_password:%s,ad_password:%s,x:%s,m:%s,ou:%s,phone:%s"%(email_address,mail_password,ad_password,family,given,ou,phone))
		except Exception as err:
			return err
		else:
			return run_result

class Alicloud_API:
	#阿里云相关接口
	def sent_sms(to_address,from_sign,TemplateCode,TemplateParam):
	#发送短信接口
		try:
			run_result=Alicloud_sms.SMS.sent_sms(to_address,from_sign,TemplateCode,TemplateParam)
			save_log("sent_sms to_address:%s,from_sign:%s,TemplateCode:%s,TemplateParam:%s"%(to_address,from_sign,TemplateCode,TemplateParam))
		except Exception as err:
			return err
		else:
			return run_result
			

@csrf_exempt
def get_data(request):

	try:
		if request.META.get('HTTP_X_FORWARDED_FOR'):
			ip = request.META.get("HTTP_X_FORWARDED_FOR")
		else:
			ip = request.META.get("REMOTE_ADDR")
	except Exception as err:
		ip = 'unknow IP address'
	save_log("\n")
	save_log("Request from IP:%s"%ip)
	
	if request.method != "POST":	# 定义post接口
		save_log("Receive WRONG request, not POST method")
		return JsonResponse({"msg": "Receive WRONG request, not POST method"})
		
	try:
		SECRET = request.POST.get("SECRET")
		API_POST_METHOD = request.POST.get("API_POST_METHOD")
		#sha256后的SECRET为：ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85
		
		if SECRET==None:
			run_result='SECRET EMPTY'
			save_log("run_result:%s"%run_result)
			return JsonResponse({"msg": "%s"%run_result})
		save_log("GET SECRET(sha256):%s"%hashlib.sha256(SECRET.encode()).hexdigest())
		
		if (hashlib.sha256(SECRET.encode()).hexdigest() != 'ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85'):
			run_result='Invalid SECRET'
			save_log("run_result:%s"%run_result)
			return JsonResponse({"msg": "%s"%run_result})
		save_log("SECRET CHECK PERMIT")
		
		if API_POST_METHOD==None:
			run_result='API_POST_METHOD EMPTY'
			save_log("run_result:%s"%run_result)
			return JsonResponse({"msg": "%s"%run_result})
		save_log("GET API_POST_METHOD:%s"%API_POST_METHOD)
		
		run_result='Invalid API_POST_METHOD code'
		if API_POST_METHOD=='201909230001':
			name = request.POST.get("name")
			run_result=Microsoft_AD.Add_VPN_User_Group(name)
		
		if API_POST_METHOD=='201909270001':
			name = request.POST.get("name")
			run_result=Microsoft_AD.Add_VPN_bussiness1_Group(name)
		
		if API_POST_METHOD=='201909270002':
			name = request.POST.get("name")
			run_result=Microsoft_AD.remove_VPN_bussiness1_Group(name)
		
		if API_POST_METHOD=='201910280001':
			name = request.POST.get("name")
			password = request.POST.get("password")
			run_result=Microsoft_AD.reset_password(name,password)
			
		if API_POST_METHOD=='201910280002':
			name = request.POST.get("name")
			password = request.POST.get("password")
			run_result=Google_Gsuit.reset_password(name,password)
			
		if API_POST_METHOD=='201910300001':
			name = request.POST.get("name")
			run_result=Google_Gsuit.suspend_user(name)
			
		if API_POST_METHOD=='201911280001':
			name = request.POST.get("name")
			database_id = request.POST.get("database_id")
			if database_id=='1':
				database_group_name='database'
			if database_id=='0':
				database_group_name='database_back_8'
			run_result=Microsoft_AD.add_database_group(name,database_group_name)
			
		if API_POST_METHOD=='202007110001':
			email_address=request.POST.get("email_address")
			mail_password=request.POST.get("mail_password")
			ad_password=request.POST.get("ad_password")
			family=request.POST.get("family")
			given=request.POST.get("given")
			ou=request.POST.get("ou")
			phone=request.POST.get("phone")
			run_result=Add_User_New_employee.add_user(email_address,mail_password,ad_password,family,given,ou,phone)
			
		if API_POST_METHOD=='202007111001':
			to_address=request.POST.get("to_address")
			from_sign=request.POST.get("from_sign")
			TemplateCode=request.POST.get("TemplateCode")
			TemplateParam=request.POST.get("TemplateParam")
			run_result=Alicloud_API.sent_sms(to_address,from_sign,TemplateCode,TemplateParam)
			
	except Exception as err:
		save_log("run_result:%s"%err)
		return JsonResponse({"msg": "%s"%err})
	else:
		save_log("run_result:%s"%run_result)
		return JsonResponse({"msg": "%s"%run_result})
