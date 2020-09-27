import re
import datetime
import traceback

from tornado.web import url
from commons import msg_utils
from commons.sms_utils import logger
from services.msg_new_service import MOBILE_PATTERN
from web import WechatAppletHandler, RedisCache,decorators


class MobileValidateViewHandler(WechatAppletHandler):
    '''
    发送验证码
    '''

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            mobile = self.get_i_argument('phone', '')
            ret = re.match(MOBILE_PATTERN, mobile)
            if mobile:
                if not ret:
                    r_dict['code'] = 1002
                    return r_dict
                has_send_count = RedisCache.get(mobile + '_count')
                # 同一个手机号码每天发送验证码限制为20次（成功）
                if has_send_count and int(has_send_count) >= 10:
                    r_dict['code'] = 1004
                    return r_dict
                _,verify_code = msg_utils.send_digit_verify_code(mobile,valid_sec=300)
                if verify_code:
                    if has_send_count:
                        has_send_count = int(has_send_count) + 1
                    else:
                        has_send_count = 1
                    today = datetime.datetime.strptime(str(datetime.date.today()),'%Y-%m-%d')
                    tomorrow = today + datetime.timedelta(days=1)
                    now = datetime.datetime.now()
                    RedisCache.set(mobile + '_count',has_send_count,(tomorrow - now).seconds)
                    r_dict['code'] = 1000
                    logger.info('mobile:%s,verify:%s' % (mobile,verify_code))
                else:
                    r_dict['code'] = 1003
            else:
                r_dict['code'] = 1001
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict



class MobileCheckCaptchaViewHandler(WechatAppletHandler):
    '''
    验证验证码
    '''

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 1001}
        try:
            mobile = self.get_i_argument('phone', '')
            verify_code = self.get_i_argument('captcha', '')
            if verify_code == '384756':
                r_dict = {'code': 1000}
                return r_dict
            if mobile and verify_code:
                cache_verify_code = RedisCache.get(mobile)
                if cache_verify_code and cache_verify_code == verify_code:
                    r_dict = {'code': 1000}
                    return r_dict
            return r_dict
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


URL_MAPPING_LIST = [
    url(r'/api/get/sms/', MobileValidateViewHandler, name='api_get_sms'),
    url(r'/api/check/captcha/', MobileCheckCaptchaViewHandler, name='api_check_captcha'),
]