# Telegram RSS Bot
- [开始使用](#开始使用)
- [配置](#配置)
- [命令行参数](#命令行参数)
## 开始使用
安装依赖库，配置好设置里的`token`参数，然后运行`rssbot.py`即可。
## 配置
新建`settings.txt`文件，所有配置都按照`key=value`的格式写。  
如果值是布尔型，`true`对应`1`，`false`对应`0`。  
例如：
```text
token=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
maxCount=200
downloadMediaFile=1
sendFileURLScheme=0
rssbotLib=rssbot.dll
```
- [token](#token)
- [maxCount](#maxcount)
- [minTTL](#minttl)
- [maxTTL](#maxttl)
- [maxRetryCount](#maxretrycount)
- [telegramBotApiServer](#telegrambotapiserver)
- [downloadMediaFile](#downloadmediafile)
- [sendFileURLScheme](#sendfileurlscheme)
- [rssbotLib](#rssbotlib)
- [databaseLocation](#databaselocation)
- [retryTTL](#retryttl)
- [botOwnerList](#botownerlist)
- [miraiApiHTTPServer](#miraiapihttpserver)
- [miraiApiHTTPAuthKey](#miraiapihttpauthkey)
- [miraiApiQQ](#miraiapiqq)
### token
必填参数。Telegram Bot API Token。向[@BotFather](https://t.me/BotFather)请求新建Bot，即可得到。
### maxCount
可选参数。一个RSS订阅源中支持的最大条数，超出部分将会自动被忽略。默认值为`100`。
### minTTL
可选参数。最小更新间隔。默认值为`5`。单位为分。
### maxTTL
可选参数。最大更新间隔。默认值为`1440`。单位为分。如果该值小于`minTTL`，将会自动设为`minTTL`。
### maxRetryCount
可选参数。使用Telegram Bot API发送信息发生错误时的最大重试次数。默认值为5。
### telegramBotApiServer
可选参数。Telegram Bot API Server地址，例如`http://localhost:8081`。设置自建服务器地址后可以启用部分功能。[有关自建Telegram Bot API Server的信息。](https://core.telegram.org/bots/api#using-a-local-bot-api-server)
### downloadMediaFile
可选参数。在发送媒体文件前是否先下载。如果使用官方API地址，使用该方式最大可以发送50M的视频/文件和10M的图片。默认值为否(`0`)。  
注：即使使用自建Telegram Bot API Server，如果不启用此功能，依旧会受到最大20M文件或5M图片的限制。
### sendFileURLScheme
可选参数。是否使用本地文件（`file:///`）协议发送媒体。需要确保启用`downloadMediaFile`并且使用的是本地的Telegram Bot API Server（`telegramBotApiServer`）。默认值为否(`0`)。
### rssbotLib
可选参数。[RSSBotLib](https://github.com/lifegpc/rssbotlib)的共享库位置。设置并且成功加载共享库后，默认启用以下功能：
- 发送视频时附带时长，视频分辨率大小信息（在视频文件大于10MB时非常有用）。
### databaseLocation
可选参数。数据库位置。默认值为`data.db`。
### retryTTL
可选参数。RSS更新发生错误后，再次更新的间隔时间。支持以`,`为分隔的列表，分别表示第一次更新错误后等待的时间、第二次更新错误后等待的时间……超过列表范围会采用列表中的最后一个值。  
例如设置为`5,15`，则第一次更新错误后等待5分钟，第二次更新错误后等待15分钟，第三次更新错误后等待15分钟……  
默认值为`30`。单位为分。
### botOwnerList
可选参数。具有特殊权限的用户ID，这些用户可以使用部分特殊功能。可以使用`,`分隔两个不同的ID。
特殊权限：
- 可以强制更新RSS
### miraiApiHTTPServer
可选参数。指定[mirai-api-http](https://github.com/project-mirai/mirai-api-http)服务器位置。例如`http://localhost:8081`。可用来发送QQ消息。设置后必须设置[`miraiApiHTTPAuthKey`](#miraiapihttpauthkey)和[`miraiApiQQ`](#miraiapiqq)
### miraiApiHTTPAuthKey
可选参数。指定mirai-api-http的[AuthKey](https://github.com/project-mirai/mirai-api-http#开始使用)。
### miraiApiQQ
可选参数。已在mirai登录的QQ号。
## 命令行参数
```text
--rebuild-hashlist 重建hashList
--exit-after-rebuild 再重建hashList后退出
-c/--config <file> 从指定文件中读取配置
```

