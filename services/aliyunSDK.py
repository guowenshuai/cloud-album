'''
短信业务调用接口示例，版本号：v20170525
Created on 2017-06-12
'''
import random
import json
import time
import uuid

# 阿里云短信接口
from time import sleep

ACCESS_KEY_ID = "xxxxxxxxxxx"
ACCESS_KEY_SECRET = "xxxxxxxxxxxxxxxxxxxxxx"
# 注意：不要更改
REGION = "cn-hangzhou"
PRODUCT_NAME = "Dysmsapi"
DOMAIN = "dysmsapi.aliyuncs.com"

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.profile import region_provider
from commons.aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
# from application.settings import ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION, DOMAIN, PRODUCT_NAME

acs_client = AcsClient(ACCESS_KEY_ID,ACCESS_KEY_SECRET,REGION)
region_provider.modify_point(PRODUCT_NAME,REGION,DOMAIN)

def send_sms(phone_numbers,code):
    '''
    发送短信接口，在需要使用的地方引用该模板，调用该接口即可
    :param phone_numbers: 发送的手机号码
    :param sign_name: 应用名
    :param template_code: 模板名称
    :param template_param: 模板变量参数
    :return:
    '''
    sign_name = "苏州星际云通" # 应用名称
    template_code = "SMS_150786099" # 模板名称
    template_param = json.dumps({'code':code}) # 模板变量参数

    business_id = uuid.uuid1()
    smsRequest = SendSmsRequest.SendSmsRequest()
    smsRequest.set_TemplateCode(template_code) # 申请的短信模板编码，必填

    # 短信模板变量参数
    if template_param is not None:
        smsRequest.set_TemplateParam(template_param)
    smsRequest.set_OutId(business_id) # 设置业务骑牛流水号，必填
    smsRequest.set_SignName(sign_name)  # 短信签名
    smsRequest.set_PhoneNumbers(phone_numbers) # 短信发送的号码列表，必填
    # 调用短信发送接口，返回json
    try:
        print(smsRequest,'0')
        smsResponse =  acs_client.do_action_with_exception(smsRequest)
        smsResponse = smsResponse.decode('utf-8')
        smsResponse = json.loads(smsResponse)
        print(smsResponse,'1.5')
        if smsResponse['Code']!="OK":
            print(smsResponse['Message'])
        time.sleep(10)
        print(smsResponse,'1')
    except Exception as e:
        print(e)
    # TODO 业务处理
    else:
        print(smsResponse,'3')
        return smsResponse
    return None



# 随机短信验证码
def get_code():
    return random.randrange(1000,9999)

if __name__ == '__main__':
    send_sms(1762189858, 1234)
