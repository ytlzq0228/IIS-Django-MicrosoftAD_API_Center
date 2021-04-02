# encoding=utf-8
import paramiko
import time
import re
import sys
import json

ssh_client = paramiko.SSHClient()
ssh_client.load_system_host_keys()
know_host = paramiko.AutoAddPolicy()
ssh_client.set_missing_host_key_policy(know_host)
deviceip = 'nas.csdn.net'
#修改nasIP地址
SU_PASSWD='**************'
#修改admin用户的密码
ssh_client.connect(deviceip,22,'admin',SU_PASSWD,allow_agent=False,look_for_keys=False)
ssh_shell = ssh_client.invoke_shell()

permission_dict={
'MA':'rwxpdDaARWcCo:fd--',
'RO':'r-x---a-R-c--:fd--',
'RW':'rwxpdDaARWc--:fd--',
}


class ssh_operation:


	def check_CLI_endswith(endswith_str,last_return):
		try:
			lines=[last_return]
			if last_return.endswith(endswith_str):
				return last_return
			else:
				i=0
				while True:
					i=i+1
					if i>50:
						break;
					line = ssh_shell.recv(1024)
					#print(line.decode(encoding='utf-8', errors='strict'))
					if line and line.decode(encoding='utf-8', errors='strict').endswith(endswith_str):
						break;
					lines.append(line.decode(encoding='utf-8', errors='strict').replace('\r',''))
					time.sleep(0.1)
				result = ''.join(lines)
				return result
		except Exception as err:
			raise err
	
	def sent_commadn_and_receive(ssh_command):
		try:
			ssh_shell.send('\n')
			ssh_shell.send(ssh_command+' \ncommend_end')
			time.sleep(0.2)
			result=ssh_shell.recv(65535).decode(encoding='utf-8', errors='strict').replace('\r','')
			#print(result)
		except Exception as err:
			raise err
		else:
			return result
	

class synology_nas:
	def get_su_permission():
		try:
			while True:
				ssh_shell.send('sudo -s\n')
				time.sleep(0.2)
				temp_return=ssh_shell.recv(128).decode(encoding='utf-8', errors='strict').replace('\r','')
				#print(temp_return)
				if temp_return.endswith('assword: '):
					ssh_shell.send(SU_PASSWD+'\n')
					temp_return=ssh_shell.recv(128).decode(encoding='utf-8', errors='strict').replace('\r','')
					ssh_operation.check_CLI_endswith('# ',temp_return)
					break;
				elif temp_return.endswith('# '):
					break;
				time.sleep(3)
		except Exception as err:
			raise err
			
	def list_synoshare():
		try:
			list_synoshare_result=ssh_operation.sent_commadn_and_receive('find /volume1/ -maxdepth 2 -type d')
			list_synoshare_result=ssh_operation.check_CLI_endswith('$ commend_end',list_synoshare_result)
			#print(list_synoshare_result)
			return_result=[]
			for line in list_synoshare_result.split('\n'):
				#print(line)
				if '@' not in line and 'Permission denied' not in line and '#' not in line and 'maxdepth' not in line:
					return_result.append(line.replace('/volume1',''))
			if '/' in return_result:
				return_result.remove('/')
			if '' in return_result:
				return_result.remove('')
		except Exception as err:
			raise err
		else:
			return return_result

	def list_synouser():
		try:
			synology_nas.get_su_permission()
			list_synouser_result=ssh_operation.sent_commadn_and_receive('synouser --enum all')
			list_synouser_result=ssh_operation.check_CLI_endswith('# commend_end',list_synouser_result)
			return_result=[]
			for line in list_synouser_result.split('\n'):
				#print(line)
				if '#' not in line and '--enum' not in line and ':' not in line:
					return_result.append(line)
			if '' in return_result:
				return_result.remove('')
		except Exception as err:
			raise err
		else:
			return return_result


	def check_acl_permission(dir_path,username,user_permission):
		try:
			check_result=False
			synology_nas.get_su_permission()
			check_acl_permission_result=ssh_operation.sent_commadn_and_receive('synoacltool -get /volume1%s'%dir_path)
			check_acl_permission_result=ssh_operation.check_CLI_endswith('# commend_end',check_acl_permission_result)
			check_acl_permission_result=check_acl_permission_result.split('\n')
			#print(check_acl_permission_result)
			for line in check_acl_permission_result:
				if username in line and user_permission in line:
					check_result=True
		except Exception as err:
			raise err
		else:
			return check_result
			
	def set_acl_permission(dir_path,username,user_permission):
		try:
			user_permission=permission_dict[user_permission]
			synology_nas.get_su_permission()
			if synology_nas.check_acl_permission(dir_path,username,user_permission):
				return_result={'Current_ACL':'Already Exist','Return_Result':'OK'}
			else:
				set_acl_permission_result=ssh_operation.sent_commadn_and_receive('synoacltool -add /volume1%s user:%s@csdn.net:allow:%s:fd--'%(dir_path,username,user_permission))
				set_acl_permission_result=ssh_operation.check_CLI_endswith('# commend_end',set_acl_permission_result)
				#print(set_acl_permission_result)
				if synology_nas.check_acl_permission(dir_path,username,user_permission):
					return_result={'Current_ACL':'NOT Exist and Add now','Return_Result':'OK'}
				else:
					return_result={'Current_ACL':'NOT Exist','Return_Result':'Something Wrong~~~~'}
		except Exception as err:
			raise err
		else:
			return return_result





def main():
	try:
		
		#result=synology_nas.set_acl_permission('/bak/100MEDIA/','linjy','RW')
		#print(result)
		#result=synology_nas.list_synoshare()
		#print(result)
		#for i in result:
		#	print(i)
		#测试使用
		

	except Exception as err:
		raise err

if __name__ == '__main__':
	main()
