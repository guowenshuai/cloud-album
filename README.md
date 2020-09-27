
> #### 拉取代码及初步操作
> * git clone https://gitee.com/yaochangfei/base.git
> * pycharm打开项目 创建虚拟环境（python3.6.*）
> * pip install -r requirements.txt 
> * mkdir logs （创建日志目录，该文件不在git上）

> #### 拉取代码及初步操作
> * local_settings.py 修改mongodb与redis相关配置

> #### 初始化数据
> * python init_data.py

> #### 本地服务管理：
> * 启动：python __main__.py -port=5555

> #### 本地任务管理：
> * 启动：
>    + celery worker -A tasks -l INFO
>    + celery beat -A tasks -l INFO


> #### 调用任务的方式
> * function.delay(*args, *kwargs)

> #### 服务器服务管理：
> * 启动：python main.py server start 5555 4
> * 停止：python main.py server stop 5555 4
> * 重启：python main.py server restart 5555 4

> #### 服务器任务管理
> * 启动任务：python main.py tasks start
> * 停止任务：python main.py tasks stop


> #### 解决PyCurl安装错误
> * yum install python36-devel
> * yum install openssl openssl-devel
> * yum install libcurl-devel
> * export PYCURL_CURL_CONFIG=/usr/bin/curl-config
> * export PYCURL_SSL_LIBRARY=nss
> * easy_install pycurl



