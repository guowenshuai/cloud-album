# !/usr/bin/python
# -*- coding:utf-8 -*-

import os
import platform
import traceback

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))

OS = platform.system()

# 服务器配置
SERVER_HOST = '***.com'
SERVER_PORT = 443
SERVER_PROTOCOL = 'https' if SERVER_PORT == 443 else 'http'
RACE_REPORT_HOST = '***.com'

# 缓存设置
REDIS_CLUSTER = True
REDIS_NODES = [
    '10.28.146.109:8812',
    '10.28.252.160:8812',
    '10.29.190.8:8812'
]
REDIS_OPTIONS = dict(
    password=None,
    encoding='utf-8',
    decode_responses=False,
    max_connections=10 * 1024
)

# Celery任务Redis配置
REDIS_TASK_HOST = '10.29.192.21'
REDIS_TASK_PORT = 8813
REDIS_TASK_DB = 0

# 数据库配置
DB_ADDRESS_LIST = [
    '10.29.182.7:9912',
    '10.29.192.72:9912',
    '10.28.142.24:9912',
    '10.28.148.68:9912',
    '10.81.246.253:9912',
    '10.81.245.104:9912'
]
DB_NAME = '***'  # 数据名
AUTH_USER_NAME = '***'  # 用户名
AUTH_USER_PASSWORD = '***'  # 密码
AUTH_DB_NAME = 'admin'  # 检验用户数据库
OPT_MIN_POOL_SIZE = 16  # 连接最小数量
OPT_MAX_POOL_SIZE = 960  # 连接最大数量
OPT_CONNECT_TIMEOUT_MS = 1000 * 3  # 连接超时时间, 单位: 毫秒
OPT_WAIT_QUEUE_TIMEOUT_MS = 1000 * 10  # 连接队列等待超时时间, 单位: 毫秒
OPT_REPLICA_SET_NAME = '****'  # 副本集名称
OPT_READ_PREFERENCE = 'secondaryPreferred'  # 副本集读写方式, primary|primaryPreferred|secondary|secondaryPreferred
OPT_WRITE_SYNC_NUMBER = 1  # 阻塞写操作直到同步指定数量的从服务器为止, 0: 禁用写确认, 使用事务是该值必须大于0，且小于等于从服务器数量
OPT_DISTRIBUTED_CACHED_ENABLE = True  # 启用数据库分布式缓存， 开启此选项请启用缓存

# 服务框架配置
SESSION_SECRET_KEY = 'A1D91B98-93DD-4F69-B042-2CFBEE1DFC31'
SESSION_TIMEOUT = 45 * 60
COOKIE_SECRET_KEY = '6C3C3D6F-A5C3-4584-BE59-9B6AF70CBF24'
XSRF_COOKIES = True
XSRF_COOKIE_VERSION = 2
AUTO_ESCAPE = None
COMPRESS_RESPONSE = True
TEMPLATE_PATH = os.path.join(SITE_ROOT, 'templates')
STATIC_HASH_CACHE = True
STATIC_PATH = os.path.join(SITE_ROOT, 'static')
STATIC_URL_PREFIX = '/static/'
AUTO_RELOAD = False
NUM_PROCESSES = 0  # 服务启动进程数，0：依据CPU数量启用进程数

# 系统日志
LOG_PATH = os.path.join(SITE_ROOT, 'logs')
LOG_LEVEL = 'ERROR'  # DEBUG|INFO|WARNING|ERROR|NONE
LOG_STDERR = False  # 输出到标准错误流
LOG_NAME = 'base.log'  # 主动日志
LOG_NAME_ACCESS = 'access.log'  # 执行日志

# 存储系统附件的目录
UPLOAD_FILES_PATH = os.path.join(SITE_ROOT, 'static', 'files')

# 邮件服务
MAIL_SERVER_HOST = 'smtp.exmail.qq.com'
MAIL_SERVER_PORT = 25
MAIL_SERVER_USER = 'no-reply.crspn@idiaoyan.com'
MAIL_SERVER_PASSWORD = 'Crspn123'

# 短信息
SMS_SIGNATURE = '【星际云通】'

# 临时目录
TEMP_PATH = os.path.join(SITE_ROOT, 'temp')

# 请求中间件设置
REQUEST_HANDLER_MIDDLEWARE_LIST = [
    # 'middleware.verification_code_limit_middleware.VerificationCodeLimitMiddleware'
]

# 分布式任务配置
SCHEDULE_IN = False  # 是否包含排班任务
WORKER_CONCURRENCY = 8  # 建议CPU数量整数倍
TASKS_FUNC_MODULE_CFG_LIST = [
    # ('任务方法所在模块', '任务队列名称'),
    ('tasks.instances.task_send_msg', 'send_msg'),

]

# 微信服务号设置
APP_ID = ''  # 应用ID
APP_SECRET = ''  # 应用密钥
TOKEN = ''  # Token(令牌)

# 小程序设置
MINI_APP_ID = 'wx202ee756b5ac0eec'  # 应用ID
MINI_APP_SECRET = 'b426077175ebd1983d3e47f84d21de86'  # 应用密钥


# 导入本地配置以覆盖系统配置
try:
    if os.path.exists(os.path.join(SITE_ROOT, 'local_settings.py')):
        from local_settings import *

        SERVER_PROTOCOL = 'https' if SERVER_PORT == 443 else 'http'
except RuntimeError:
    traceback.format_exc()
DOMAIN_PORT = SERVER_PORT
if DOMAIN_PORT == 80 or DOMAIN_PORT == 443:
    if DOMAIN_PORT == 80:
        SITE_URL = 'http://%s' % SERVER_HOST
    else:
        SITE_URL = 'https://%s' % SERVER_HOST
else:
    SITE_URL = 'http://%s:%s' % (SERVER_HOST, DOMAIN_PORT)
