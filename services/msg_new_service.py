# !/usr/bin/python
# -*- coding:utf-8 -*-
import datetime
import re
import json
import traceback
import uuid

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.profile import region_provider
from commons.aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
from db.models import InstantSms

STATUS_MOBILE_MSG_SUCCEED = 1  # 发送成功
STATUS_MOBILE_MSG_FAILED = 2  # 发送失败
STATUS_MOBILE_MSG_SYSTEM_ERROR = 0  # 系统异常
STATUS_MOBILE_MSG_NUMBER_NULL = -1  # 手机号为空
STATUS_MOBILE_MSG_NUMBER_ERROR = -2  # 手机号格式错误
STATUS_MOBILE_MSG_CONTENT_NULL = -3  # msg内容为空

# 阿里云短信接口
ACCESS_KEY_ID = "xxxxxxxxxx"
ACCESS_KEY_SECRET = "xxxxxxxxxxxxxxxxxxxxx"
REGION = "cn-hangzhou"
PRODUCT_NAME = "Dysmsapi"
DOMAIN = "dysmsapi.aliyuncs.com"
SIGN_NAME = "苏州星际云通"  # 应用名称
TEMPLATE_CODE = "SMS_150786099"  # 模板名称
MOBILE_PATTERN = r"^1\d{10}$"
ACS_CLIENT = AcsClient(ACCESS_KEY_ID,ACCESS_KEY_SECRET,REGION)
region_provider.modify_point(PRODUCT_NAME,REGION,DOMAIN)



def send_instant_sms(mobile, code, time):
    """
    发送文本信息
    @param mobile: 号码
    @param code: 验证码
    @param time: 过期时间
    @return:
    """
    status = STATUS_MOBILE_MSG_SYSTEM_ERROR
    exception = ""
    try:
        if not code or not time:
            return STATUS_MOBILE_MSG_CONTENT_NULL
        if not mobile:
            return STATUS_MOBILE_MSG_NUMBER_NULL
        else:
            if not re.match(MOBILE_PATTERN, mobile.strip()):
                return STATUS_MOBILE_MSG_NUMBER_ERROR

        smsRequest = SendSmsRequest.SendSmsRequest()
        smsRequest.set_TemplateCode(TEMPLATE_CODE)  # 申请的短信模板编码，必填
        template_param = json.dumps({'code': code})  # 模板变量参数
        # 短信模板变量参数
        smsRequest.set_TemplateParam(template_param)
        business_id = uuid.uuid1()
        smsRequest.set_OutId(business_id)  # 设置业务骑牛流水号，必填
        smsRequest.set_SignName(SIGN_NAME)  # 短信签名
        smsRequest.set_PhoneNumbers(mobile)  # 短信发送的号码列表，必填
        # 调用短信发送接口，返回json
        smsResponse = ACS_CLIENT.do_action_with_exception(smsRequest)
        smsResponse = smsResponse.decode('utf-8')
        smsResponse = json.loads(smsResponse)
        if smsResponse['Code'] == "OK":
            status = STATUS_MOBILE_MSG_SUCCEED
        else:
            status = STATUS_MOBILE_MSG_FAILED
            exception = smsResponse['Message']
    except Exception:
        exception = traceback.format_exc() + exception

    # 存储发送历史
    try:
        instant_sms = InstantSms(sms_server=DOMAIN, account=ACCESS_KEY_ID,
                                 post_dt=datetime.datetime.now(),
                                 status=status, mobile=mobile, content=code, exception=exception)
        instant_sms.sync_save()
    except Exception:
        pass
    return status


if __name__ == '__main__':
    send_instant_sms('17621898587', '123456', '1分钟')
