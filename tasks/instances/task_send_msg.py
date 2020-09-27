# !/usr/bin/python
# -*- coding:utf-8 -*-


from logger import log_utils
from services.msg_new_service import send_instant_sms
from tasks import app

logger = log_utils.get_logging('tasks_send_sms', 'tasks_send_sms.log')


@app.task(bind=True, queue='send_sms')
def send_sms(self, mobile, code, valid_sec):
    print(mobile)
    print(code)
    print(valid_sec)
    if mobile and valid_sec and code:
        logger.info('START: Send SMS mobile=%s, code=%s, valid_sec=%s' % (mobile, code, valid_sec))
        status = send_instant_sms(mobile=mobile, code=code, time=valid_sec)
        print(status, 'status')
        logger.info('[%s] SEND SMS: status=%s, to=%s, content=%s' % (
        self.request.id, status, mobile, '您的本次验证码为：%s, 有效期%s秒' % (str(code), valid_sec)))
        return status
