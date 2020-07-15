本文主要介绍，如何通过Django+IIS+Python构建一个接口中心。让ERP或者OA系统可以通过API的方式管理AD域控服务器。同时延伸出来，可以使用Django调用其他的Python脚本，实现更为丰富的功能功能
本文所示例子实际落地场景举例：
**`某用户申请VPN权限，企业内部ERP流程审批完成后，ERP系统直接调用接口将此员工AD域账号加入VPN用户群组。`**
本文主要涉及的知识点：
>1、IIS+Django部署
2、IIS应用处理模块
3、Django请求处理逻辑
4、Django调用本地Python脚本并处理返回结果
5、Python通过os.system调用命令行实现AD域控制器管理

更好的阅读体验，可以移步至
[【逗老师带你学IT】Django+IIS+Python构建微软AD域控API管理中心](https://ctsdn.blog.csdn.net/article/details/107361857)

@[TOC](目录)
# 一、项目整体概况

## 1、Django框架简介
关于Django框架，网内有其他大大的文章，本文中简单较少一下
传送门：[Django框架介绍及配置](https://blog.csdn.net/weixin_43751803/article/details/87906148)

Django，发音为[`dʒæŋɡəʊ]，出门跟别人聊天，念成[底江狗]

django是用python语言写的开源web开发框架，并遵循MVC设计。

诞生历史: 劳伦斯出版集团为了开发以新闻内容为主的网站，而开发出来了这个框架，于2005年7月在BSD许可证下发布。这个名称来源于比利时的爵士音乐家DjangoReinhardt，他是一个吉普赛人，主要以演奏吉它为主，还演奏过小提琴等。

由于Django在近年来的迅速发展，应用越来越广泛，被著名IT开发杂志SDTimes评选为2013SDTimes100，位列"API、库和框架"分类第6位，被认为是该领域的佼佼者。

django框架是一个web框架, 而且是一个后端框架程序, 它不是服务器, 需要注意
django框架帮我们封装了很多的组件, 帮助我们实现各种功能, 具有很强的扩展性.

## 2、本例文件结构
**本例涉及的代码已上传Github**
[Public_Share_Project/IIS+Django+MicrosoftAD_API_Center/](https://github.com/ytlzq0228/IIS-Django-MicrosoftAD_API_Center)
**项目文件结构：**
./ApiSite 目录主要涉及Django自身的相关流程
./api 目录为用户自定义的接口页面，接口URL http://x.x.x.x/api
./log 目录为日志目录
./Python_Program 目录为自定义的第三方Python脚本的存放目录
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715161112277.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)

# 二、环境安装和准备
## 1、Windows+IIS+AD微软套件
在本实例中，由于Windows权限控制，我们必须**在AD域控制器上直接运行**bat命令才能对AD域内资源进行管理。

因此我们的服务端必须部署在一台Windows服务器上，并且这台服务器在域内角色需要是**DC和GC**，且可以是**只读**的DC或GC。

### 1.1 Windows 服务器
建议选择Server 2012以上版本，具体系统版本尽可能与其他域控制器版本一致。本例中使用Windows Server 2016
### 1.2 IIS 服务器
由于操作系统必须选定为Windows Server，因此选则与操作系统版本匹配的IIS即可，本例中使用IIS 10.0
特别需要注意的是，本实例必须使用Web服务器>应用程序开发>CGI功能。在部署IIS时请务必勾选。
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715192059650.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
### 1.3 Microsoft AD域控制器
将新准备的Windows Server服务器加入现有AD域，并且设置成DC或者GC角色的域控制器。
如果你看完本文之后，发现仅需要Django+Python的功能，不需要管理AD域。那么此服务器可以不加域，甚至可以选择其他前端服务器。比如CentOS+Django

## 2、Python环境安装
访问[python.org](https://www.python.org/downloads/)下载Windows版的Python，本例中使用目前最新的Python 3.8版本。

## 3、Python wfastcgi依赖环境安装
fastcgi
在Windows下，我们没法使用uwsgi，但我们可以使用wfastcgi替代它，打开CMD窗口，输入命令安装wfastcgi：

```bash
pip install wfastcgi
```

安装成功之后，通过下面命令启动它：

```bash
wfastcgi-enable
```
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715193030493.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
如上图，启动成功之后，它会把Python路径和wfastcgi的路径显示出来，我们需要把这个路径复制出来，保存好，后边用得着。
```bash
c:\users\administrator\appdata\local\programs\python\python38-32\python.exe|c:\users\administrator\appdata\local\programs\python\python38-32\lib\site-packages\wfastcgi.py
```

注意：上面的路径，是由Python解释器的路径和“|”以及“wfastcgi.py”文件路径组成。

## 3、Django环境安装
[https://www.djangoproject.com/download/](https://www.djangoproject.com/download/)]
使用下面命令安装最新版本Django

```bash
pip install Django==3.0.8
```

## 4、PIP依赖包安装

# 三、服务端配置
## 1、IIS配置和fastCGI配置
### 1.1 添加新网站
打开IIS管理器，右键“网站”，点击“添加网站”
这里，我们添加一个名为Django_API的网站，物理存储路径在C盘根目录的\Django_API下。
![在这里插入图片描述](https://img-blog.csdnimg.cn/202007151823369.png)
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715182440296.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
### 1.2 配置处理程序映射使用fastCGI
#### 1.2.1 使用图形界面方式
打开建立的网站，选择“处理程序映射”，然后选择“添加模块映射”
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715183137414.png)            ---------->![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715183151773.png)
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715183011138.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
按照上图配置，可执行文件中填的前面一部分是python.exe的路径，中间用“|”分割，后面一部分是wfastcgi.py文件的路径。
此信息在本文“二、3、Python wfastcgi依赖环境安装”中提到，运行wfastcgi-enable启动wfastcgi之后系统给出的路径信息。
#### 1.2.2 修改配置文件方式
编辑网站根目录下的web.conf文件，按照下文示例添加，`name`字段自选，`scriptProcessor`字段按照1.2.1中所示填写
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
	<system.webServer>
   		 <handlers>
        	<add name="Python FastCGI" 
       		path="*" 
       		verb="*" 
       		modules="FastCgiModule"              
        	scriptProcessor="c:\users\administrator\appdata\local\programs\python\python38\python.exe|c:\users\administrator\appdata\local\programs\python\python38\lib\site-packages\wfastcgi.py" resourceType="Unspecified" requireAccess="Script" />
    	</handlers>
	</system.webServer>
</configuration>
```
#### 1.2.3 什么是fastCGI
fastCGI是一种CGI，CGI（通用网关接口）它是一段程序，运行在服务器上，提供同客户端HTML页面的接口，通俗的讲CGI就像是一座桥，把网页和WEB服务器中的执行程序连接起来，它把HTML接收的指令传递给服务器，再把服务器执行的结果返还给HTML页；用CGI可以实现处理表格，数据库查询，发送电子邮件等许多操作，最常见的CGI程序就是计数器。CGI使网页变得不是静态的，而是交互式的。
本例中，前端的WEB服务器为IIS，IIS接收到的数据我们需要传递给Python.exe程序运行，因此我们选择fastCGI模块来连接IIS和Python。

### 1.3 fastCGI设置
#### 1.3.1 全局设置
回到服务器，点击“fastCGI设置”，点击“添加应用程序”
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715185207879.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715185458770.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
#### 1.3.2 网站设置
回到网站，点击“应用程序设置”
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715185631340.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
添加如下三个环境变量
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715185544430.png)
### 1.4 web.conf文件范例
根据上面的配置，IIS会自动更新在根目录下的web.conf文件，如果嫌上面的配置麻烦，直接粘贴下面的web.conf文件即可

```xml
<?xml version="1.0" encoding="UTF-8"?>
    <configuration>
        <system.webServer>
            <handlers>
                <add name="Python FastCGI"
                     path="*"
                     verb="*"
                     modules="FastCgiModule"
                     scriptProcessor="c:\users\administrator\appdata\local\programs\python\python38\python.exe|c:\users\administrator\appdata\local\programs\python\python38\lib\site-packages\wfastcgi.py" 
                     #替换成真实的python和wfastcgi路径
                     resourceType="Unspecified"
                     requireAccess="Script"/>
            </handlers>
        </system.webServer>
        <appSettings>
            <add key="WSGI_HANDLER" value="django.core.wsgi.get_wsgi_application()" />
            <add key="PYTHONPATH" value="C:\API_site" /> #替换成真实的网站ROOT目录
            <add key="DJANGO_SETTINGS_MODULE" value="ApiSite.settings" /> #记住这个ApiSite，后面用得到
        </appSettings>
    </configuration>
```
### 1.5 应用程序标识设置
如下图所示，应用程序池->右键新项目->高级设置->进程模型特征->内置账户->选择LocalSystem
此操作是为应用程序可以执行本地程序授予权限，否则应用程序无法调起本地的其他程序文件。
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715190508339.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
### 1.6 web.conf解锁
IIS7之后的版本都采用了更安全的 web.config 管理机制，默认情况下会锁住配置项不允许更改。
本例中，未解锁的情况下此时直接访问会报HTTP 错误 500.19 Internal Server Error
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715193623802.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
打开CMD，在里面依次输入下面两个命令：

```powershell
%windir%\system32\inetsrv\appcmd unlock config -section:system.webServer/handlers
%windir%\system32\inetsrv\appcmd unlock config -section:system.webServer/modules
```
### 1.7 复制wfastcgi.py文件至网站根目录
将c:\users\administrator\appdata\local\programs\python\python38\lib\site-packages\wfastcgi.py复制到网站根目录下
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715194633867.png)
目前，网站根目录下存在以上两个文件
## 2、Django配置
至此，我们直接刷新网站，应该已经可以看到，程序在尝试调用网站根目录下的ApiSite模块。（“三、1.4 web.conf文件范例”中指定的模块名称）
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715195229870.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)
接下来，我们就要开始配置Django，让前面配置的fastCGI可以成功调起Django

### 1、构建ApiSite目录
**`此目录为Django运行目录`**
在网站根目录下创建ApiSite目录，如果想改成别的名字，在前面“三、1.4 web.conf文件范例”中，可以适当修改`DJANGO_SETTINGS_MODULE`字段的值。
本目录下关键文件如下：
>**log.py-**-记录日志相关，setting.py中DENUG开关为True调用此文件
**settings.py**--主功能入口，其中引用urls和api子文件夹内功能
**urls.py**--以视图形式调用最终应该程序
**wsgi.py**--wsgi处理模块

**`urls.py关键配置`**
```python
# from django.contrib import admin
from django.urls import path
from api.views import get_data	# 导入视图
#此处"api.views"对应为网站根目录下/api/views.py文件
urlpatterns = [
    # path('admin/', admin.site.urls),
    path("api", get_data),	# 定义路由（url）
    #此处"api"对应为网站根目录下/api子目录
```
**`settings.py关键配置`**

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api.apps.ApiConfig',	# 加载api应用
    #此处"api.apps"对应为网站根目录下/api/apps.py文件
]
```

### 2、构建api目录
**`此目录为实际自定义脚本运行目录`**
本例中，此目录下有两个必要的文件
apps.py--定义运行目录，本例
views.py--实际接收数据，处理数据，返回数据的程序

**`apps.py关键配置`**
```python
from django.apps import AppConfig
class ApiConfig(AppConfig):
    name = 'api'
    #返回所在目录名称
```
**`views.py关键配置`**

```python
from django.http.response import JsonResponse
def get_data(request):
        return JsonResponse({"msg": "激动的心，颤抖的手，程序终于跑起来了"})
```
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715203132617.png)
# 四、请求格式和返回格式设计
## 1、请求格式
本例中，我们使用POST形式传递表单
使用request.POST.get("par_name")方法来接收制定表单字段的值
本例锁使用的POST FORM格式体标准

```json
{

'SECRET':'PcHc******************9OkQeiY',
'API_POST_METHOD':'202007024202'
'parameter1':'value1'
'parameter2':'value3'
'parameter3':'value3'

}
```
字段解释
**`SECRET`**：机密字段，固定值，在部署前随机生成，并替换get_data(request):中的sha256校验值
hashlib.sha256(SECRET.encode()).hexdigest() != 'ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85'
**`API_POST_METHOD`**：请求方法字段，数字编码按照功能发布日期+4位顺序号书写。如202007020001表示2020年7月2日当天发布的第一个功能。对应关系参照“附表一：API_POST_METHOD字段定义表”
**`parameter`**：参数字段，按照“附表一：API_POST_METHOD字段定义表”传递制定内容的参数。
## 2、返回格式
本例中返回一个json格式结构体，用于上层程序判定调用结果。
对于调用bat执行的方法，返回的是python os.system()的返回值，正确为0，错误为-2147024809。
对于调用google，alicloud等功能执行的方法，传递Google，alicloud等接口的返回值。
**`return JsonResponse({"msg": "%s"%run_result})`**
## 3、日志格式
举例说明一段正确请求的日志格式

```
15-07-2020 12:53:16:log:Request from IP:10.0.0.100
15-07-2020 12:53:16:log:GET SECRET(sha256):ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85
15-07-2020 12:53:16:log:SECRET CHECK PERMIT
15-07-2020 12:53:16:log:GET API_POST_METHOD:202007111001
15-07-2020 12:53:17:log:sent_sms to_address:86***************,from_sign:Ω÷Ω«µÁ◊”,TemplateCode:SMS_108*******6,TemplateParam:{"name":"∂∫¿œ ¶","CNname":"*******","pass1":"***********","pass2":"************"}
15-07-2020 12:53:17:log:run_result:{"ResponseCode":"OK","NumberDetail":{"Country":"China","Region":"Beijing","Carrier":"China Unicom"},"ResponseDescription":"OK","Segments":"2","To":"86*************","MessageId":"1*********6982"}
```
举例说明几段错误请求的日志格式
```
15-07-2020 12:56:22:log:Request from IP:10.0.0.100
15-07-2020 12:56:22:log:GET SECRET(sha256):4a2aba321f57cab2057ced36fc0f0e8d0fee5256426d663271a575461a786355
15-07-2020 12:56:22:log:run_result:Invalid SECRET
15-07-2020 12:56:31:log:

15-07-2020 12:56:31:log:Request from IP:10.0.0.100
15-07-2020 12:56:31:log:GET SECRET(sha256):ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85
15-07-2020 12:56:31:log:SECRET CHECK PERMIT
15-07-2020 12:56:31:log:run_result:API_POST_METHOD EMPTY
15-07-2020 12:56:38:log:

15-07-2020 12:56:38:log:Request from IP:10.0.0.100
15-07-2020 12:56:38:log:GET SECRET(sha256):ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85
15-07-2020 12:56:38:log:SECRET CHECK PERMIT
15-07-2020 12:56:38:log:GET API_POST_METHOD:20191128000122
15-07-2020 12:56:38:log:run_result:Invalid API_POST_METHOD code
```
# 五、主要功能点介绍
## 1、Python调用bat执行AD域控管理相关功能
执行流程
**`构建dsmod命令模板->传入参数->写入test.bat->运行test.bat->获取OS运行结果->写入日志->返回运行结果`**
实际测试中发现，os.popen()方法执行`dsmod`命令时，面临权限不足的问题，无法以管理员身份管理预控资源。
因此本例中使用os.system()方法运行bat脚本。遗憾的是，os.system()方法无法获取系统的具体运行结果，仅能获取命令是否正常运行。
返回值，正确为0，错误为-2147024809

```python
def run_bat():
#bat执行函数
	try:
		run_result = os.system("test.bat >> %s\log\API_run_log.txt"%IIS_SITE_DIR)
		os.system("del test.bat")
	except Exception as err:
		return err
	else:
		return run_result

class Microsoft_AD:
	#微软AD域相关操作
	def Add_VPN_User_Group(CNname):
	#添加普通VPN用户权限
		try:
			with open("test.bat", "w") as f:
			#以写模式新建文件，写入待执行的命令
				f.write("dsquery user -upn %s@csdn.com | dsmod group \"CN=VPNUser_1,OU=VPN,DC=al,DC=com\" -addmbr"%CNname)
				#dsquery转换UPN至CNname，dsmod添加组内用户
			run_result=run_bat()
		except Exception as err:
			return err
		else:
			return run_result
def get_data(request):
	name = request.POST.get("name")
	#通过request.POST.get()方法获取POST请求中的表单内容
	run_result=Microsoft_AD.Add_VPN_User_Group(name)
	save_log("run_result:%s"%run_result)
	return JsonResponse({"msg": "%s"%run_result})
```

## 2、SECRET机密和API_POST_METHOD方法校验
本例中，没有采用Django的身份验证机制。但是为了保证接口安全，采用的SECRET机密和METHOD方法验证的机制来一定程度保证接口安全。

```python
if request.method != "POST":	#仅支持POST方法
		save_log("Receive WRONG request, not POST method")
		return JsonResponse({"msg": "Receive WRONG request, not POST method"})
		
	try:
		SECRET = request.POST.get("SECRET")
		API_POST_METHOD = request.POST.get("API_POST_METHOD")
		#sha256后的SECRET为：ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85
		
		if SECRET==None:	#校验SECRET字段是否存在，不存在直接return异常
			run_result='SECRET EMPTY'
			save_log("run_result:%s"%run_result)
			return JsonResponse({"msg": "%s"%run_result})
		save_log("GET SECRET(sha256):%s"%hashlib.sha256(SECRET.encode()).hexdigest())
		
		if (hashlib.sha256(SECRET.encode()).hexdigest() != 'ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85'):
			#校验SECRET字段是否正确，不正确直接return异常。记住，这里是校验sha256后的信息
			run_result='Invalid SECRET'
			save_log("run_result:%s"%run_result)
			return JsonResponse({"msg": "%s"%run_result})
		save_log("SECRET CHECK PERMIT")
		
		if API_POST_METHOD==None:	#校验API_POST_METHOD字段是否存在，不存在直接return异常
			run_result='API_POST_METHOD EMPTY'
			save_log("run_result:%s"%run_result)
			return JsonResponse({"msg": "%s"%run_result})
		save_log("GET API_POST_METHOD:%s"%API_POST_METHOD)
		
		run_result='Invalid API_POST_METHOD code'
		if API_POST_METHOD=='201909230001':
			name = request.POST.get("name")
			run_result=Microsoft_AD.Add_VPN_User_Group(name)
		#校验API_POST_METHOD字段是否正确，如果一条都没匹配到，run_result='Invalid API_POST_METHOD code'
	except Exception as err:
		save_log("run_result:%s"%err)
		return JsonResponse({"msg": "%s"%err})
	else:
		save_log("run_result:%s"%run_result)
		return JsonResponse({"msg": "%s"%run_result})
```
对于此种代码，需要维护一份API_POST_METHOD字段定义表，使用者在部署完成后，根据实际情况维护。
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715212732960.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3l0bHpxMDIyOA==,size_16,color_FFFFFF,t_70)


## 3、新建用户时循环检索已有用户，并给用户名+n
举例，公司内已经存在zhangsan@csdn.com和zhangsan1@csdn.com邮箱，如果新员工名字与zhangsan重名，在创建用户的时候。系统会创建循环检索已有的用户，创建zhangsan2@csdn.com的邮箱

```python
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
			#print(primaryEmail+" is a new user. Will add new user with this email")
		else:
			#print(primaryEmail+" is already exist. Try next one.")
			i=i+1
	get_new_user_info=Google_APIrequest.get_user_data(credentials,primaryEmail)
	new_user_data={ 'primaryEmail' : get_new_user_info.get('primaryEmail'), 'givenName' : get_new_user_info.get('name').get('givenName'), 'familyName' : get_new_user_info.get('name').get('familyName'), 'orgUnitPath' : get_new_user_info.get('orgUnitPath'), 'recoveryPhone':get_new_user_info.get('recoveryPhone')}
	json_new_user_data=json.dumps(new_user_data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
	return(json_new_user_data)
```

## 4、Google Gsuit接口调用，管理Google Admin网域内所有用户
本实例中引用了Google Admin的SDK调用Google 的API接口管理网域内的用户，包括用户的新建，重置密码，暂停邮箱，离职删除账号等。
具体可以参照[【逗老师带你学IT】Google Admin服务账号+API管理G suit内所有网域用户](https://ctsdn.blog.csdn.net/article/details/105682567)
## 5、SMS短信网关接口
本例中调用阿里云短信网关给新员工发送欢迎短信，以及重置域账号密码时发送【验证码】短信。
阿里云SMS网关具体使用方式，参见
[短信服务>开发指南（新版）>API概览](https://www.alibabacloud.com/help/zh/doc-detail/106344.htm)

# 六、流程测试与接口调用
以下给出一个接口测试脚本的范例，适用于测试本例接口中的各种方法。用户可以根据实际情况自行修改。

```python
import json
import urllib
import requests
import sys
import datetime
import os
def test():
	try:
		headers = {"Content-Type": "text/plain"}
		data={'SECRET':'cHcG*****************QeiYw',
		'API_POST_METHOD':'201909230001',
		'name':'doulaoshi@csdn.com'
		}
		request = requests.post(url="http://oa.api.csdn.com:8083/api",data=data)
	except Exception as err:
		raise err
	else:
		return request.text
def main():
	try:
		request_result=test()
	except Exception as err:
		print(err)
	else:
		print(request_result)
if __name__ == '__main__':
	main()
```
正确运行，返回msg如下
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200715213316584.png)
打印日志如下：

```python
15-07-2020 21:32:54:log:Request from IP:10.0.0.100
15-07-2020 21:32:54:log:GET SECRET(sha256):ae3e5f4098d40e38846f69bf83cf8f8c18a40fb27f9f7da2aa23f63241089a85
15-07-2020 21:32:54:log:SECRET CHECK PERMIT
15-07-2020 21:32:54:log:GET API_POST_METHOD:201909230001
15-07-2020 21:32:54
C:\OA_API_site>dsquery user -upn doulaoshi@csdn.com   | dsmod group "CN=VPNUser_1,OU=VPN,DC=csdn,DC=com" -addmbr 
dsmod 成功:CN=VPNUser_1,OU=VPN,DC=al,DC=com

15-07-2020 21:32:54:log:run_result:0
```

