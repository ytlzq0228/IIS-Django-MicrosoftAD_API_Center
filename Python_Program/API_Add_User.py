#coding=utf-8
import datetime
import os
import re
import sys
import time
import requests
import httplib2
import pprint
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
import googleapiclient

SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = BASE_DIR+"\\account_manager_service_account.json"
#授权空间（scope）和授权秘钥
IIS_SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save_log(result):
	try:
		now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
		f = open(IIS_SITE_DIR+"\log\Add_User_log.txt",'a')
		f.writelines("\n%s:log:%s" %(now,result))
		f.flush()
		f.close()
	except Exception as err:
		return err


def is_Chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fff':
            return True
    return False
    
class Google_APIrequest:

	def get_credentials():
		credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
		#授权应用访问G suit控制台，获取授权信息
		credentials = credentials.with_subject('accountapi@csdn.com')
		#委派管理员权限
		return credentials
		
	def get_user_data(credentials,userKey_in):
		try:
			service = build("admin", "directory_v1", credentials=credentials)
			results = service.users().get(userKey=userKey_in).execute()
		except googleapiclient.errors.HttpError as err:
			return err._get_reason()
			#异常处理方法详见google-api-python-client/googleapiclient/errors.py第47行
			#https://github.com/googleapis/google-api-python-client/blob/master/googleapiclient/errors.py
		else:
			return results

	def add_user(credentials,primaryEmail,familyName,givenName,password,orgUnitPath,PhoneNumber):
		try:
			insert_data={
				"name": {
					"familyName": familyName,
					"givenName": givenName,
					},
				 "password": password,
				 "primaryEmail": primaryEmail,
				 "changePasswordAtNextLogin": "true",
				 "orgUnitPath": orgUnitPath,
				 "recoveryPhone": PhoneNumber
				}
			service = build("admin", "directory_v1", credentials=credentials)
			results = service.users().insert(body=insert_data).execute()
		except Exception as err:
			raise err
		else:
			return results
			
class Microsoft_AD:
	
	def add_user(primaryEmail,familyName,givenName,password,orgUnitPath,PhoneNumber):
		email_fix=primaryEmail.find("@")
		email_CNname=primaryEmail[:email_fix]
		primaryEmail=email_CNname+"@al.com"
		#提出email的前缀，并更换后缀为@al.com
		if is_Chinese(familyName+givenName):
			display_name=familyName+givenName
		else:
			display_name=familyName+' '+givenName
		#分别处理中英文CNname格式
		orgUnitPath=orgUnitPath[1:]
		#去除OU_PATH第一位的/
		#os.system("dsadd user \"cn=%s,ou=%s,DC=csdn,dc=com\" -pwd %s -tel %s -upn %s" %(cnname,orgUnitPath,password,PhoneNumber,primaryEmail))
		run_result=os.system("dsadd user \"cn=%s,ou=%s,DC=csdn,dc=com\" -pwd %s -tel %s -upn %s -display \"%s\" " %(email_CNname,orgUnitPath,password,PhoneNumber,primaryEmail,display_name))
		save_log("dsadd user \"cn=%s,ou=%s,DC=csdn,dc=com\" -pwd %s -tel %s -upn %s -display \"%s\" run_result:%s" %(email_CNname,orgUnitPath,password,PhoneNumber,primaryEmail,display_name,run_result))
		

def main(primaryEmail,mail_password,ad_password,familyName,givenName,orgUnitPath,PhoneNumber):
	
	credentials=Google_APIrequest.get_credentials()
	get_user_info=""
	i=0
	email_fix=primaryEmail.find("@")
	email_CNname=primaryEmail[:email_fix]
	email_domain=primaryEmail[email_fix:]
	PhoneNumber='+'+PhoneNumber
	while get_user_info != "Resource Not Found: userKey":
		if i != 0:
			primaryEmail=email_CNname+str(i)+email_domain
			#邮箱前缀步进+1
		get_user_info=Google_APIrequest.get_user_data(credentials,primaryEmail)
		if get_user_info == "Resource Not Found: userKey":
			Google_APIrequest.add_user(credentials,primaryEmail,familyName,givenName,mail_password,orgUnitPath,PhoneNumber)#添加google邮箱
			Microsoft_AD.add_user(primaryEmail,familyName,givenName,ad_password,orgUnitPath,PhoneNumber)#添加AD域账号
			save_log(primaryEmail+" is a new user. Will add new user with this email")
		else:
			save_log(primaryEmail+" is already exist. Try next one.")
			i=i+1
	get_new_user_info=Google_APIrequest.get_user_data(credentials,primaryEmail)
	save_log(str(get_new_user_info))
	return primaryEmail
	#new_user_data={ 'primaryEmail' : get_new_user_info.get('primaryEmail'), 'givenName' : get_new_user_info.get('name').get('givenName'), 'familyName' : get_new_user_info.get('name').get('familyName'), 'orgUnitPath' : get_new_user_info.get('orgUnitPath'), 'recoveryPhone':get_new_user_info.get('recoveryPhone')}
	#json_new_user_data=json.dumps(new_user_data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
	#print(json_new_user_data)


if __name__ == '__main__':
    main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7])



