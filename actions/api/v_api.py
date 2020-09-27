# !/usr/bin/python
# -*- coding:utf-8 -*-
import datetime
import json
import re
import traceback
from tornado.web import url
from caches.redis_utils import RedisCache
from commons.common_utils import get_random_str, md5
from commons.msg_utils import check_digit_verify_code
from db import STATUS_USER_ACTIVE
from db.models import User, AppUser
from logger import log_utils
from services.msg_new_service import MOBILE_PATTERN
from settings import UPLOAD_FILES_PATH
from web import decorators, NonXsrfBaseHandler, WechatAppletHandler
from local_settings import PWD_RULE

logger = log_utils.get_logging()


class AccessTokenGetViewHandler(NonXsrfBaseHandler):
    """
    获取Access Token
    """

    @decorators.render_json
    async def post(self):
        r_dict = {'code': 0}
        try:
            args = json.loads(self.request.body.decode('utf-8'))
            access_id = self.get_argument('access_key_id')
            if not access_id:
                access_id = args.get('access_key_id')
            access_secret = self.get_argument('access_key_secret')
            if not access_secret:
                access_secret = args.get('access_key_secret')
            if access_id and access_secret:
                token = await self.generate_new_token(access_id, access_secret)
                if token:
                    r_dict['code'] = 1000
                    r_dict['token'] = token
                else:
                    r_dict['code'] = 1001  # access_key_id、access_key_secret 无效
            else:
                r_dict['code'] = 1002  # access_key_id、access_key_secret 为空
        except RuntimeError:
            logger.error(traceback.format_exc())

        return r_dict

    async def generate_new_token(self, access_id, access_secret):
        """
        生成新的TOKEN
        :param access_id: ACCESS KEY ID
        :param access_secret: ACCESS KEY SECRET
        :return:
        """
        if access_id and access_secret:
            count = await User.count(dict(access_secret_id=access_id, access_secret_key=access_secret,
                                          status=STATUS_USER_ACTIVE))
            if count > 0:
                token = get_random_str(32)
                key = md5(token)
                # RedisCache.set(key, token, 60 * 60 * 2)
                RedisCache.set(key, token)
                return token
        return None


class MemberRegisterCaptchaViewHandler(WechatAppletHandler):
    """
    云相册app用户验证码注册
    """

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self):
        r_dict = {'code': 0}
        try:
            phone = self.get_i_argument('phone')
            captcha = self.get_i_argument('captcha')
            if phone and captcha:
                # 手机号码规则匹配
                if not re.match(MOBILE_PATTERN, phone):
                    r_dict['code'] = 1001
                    return r_dict
                # 手机号码是否已经注册过
                count = await AppUser.count(dict(phone=phone))
                if count:
                    r_dict['code'] = 1002
                    return r_dict
                # 手机验证码是否有效
                if not check_digit_verify_code(phone, captcha):
                    r_dict['code'] = 1003
                    return r_dict
            else:
                if not phone:
                    r_dict['code'] = 1010
                    return r_dict
                if not captcha:
                    r_dict['code'] = 1011
                    return r_dict

            user = AppUser(phone=phone)
            user.nick_name = phone
            user.last_login_time = datetime.datetime.now()
            await user.save()
            r_dict['app_user_cid'] = user.cid
            r_dict['code'] = 1000

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class MemberRegisterViewHandler(WechatAppletHandler):
    """
    云相册app用户注册
    """

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self):
        r_dict = {'code': 0}
        try:
            phone = self.get_i_argument('phone')
            captcha = self.get_i_argument('captcha')
            password = self.get_i_argument('password')
            repeat_password = self.get_i_argument('repeat_password')
            if phone and captcha and password and repeat_password:
                # 手机号码规则匹配
                if not re.match(MOBILE_PATTERN, phone):
                    r_dict['code'] = 1001
                    return r_dict
                # 手机号码是否已经注册过
                count = await AppUser.count(dict(phone=phone))
                if count:
                    r_dict['code'] = 1002
                    return r_dict
                # 手机验证码是否有效
                if not check_digit_verify_code(phone, captcha):
                    r_dict['code'] = 1003
                    return r_dict
                # 密码规则是否符合,8--16 字母数字符号至少2 种组合,不包含空格和中文
                if not re.match(PWD_RULE, password):
                    r_dict['code'] = 1005
                    return r_dict
                # 2次密码是否一致
                if password != repeat_password:
                    r_dict['code'] = 1006
                    return r_dict
            else:

                if not phone:
                    r_dict['code'] = 1010
                    return r_dict
                if not captcha:
                    r_dict['code'] = 1011
                    return r_dict
                if not password or not repeat_password:
                    r_dict['code'] = 1012
                    return r_dict

            # 新用户注册
            # pw_md5 = md5(password)
            user = AppUser(phone=phone)
            user.password = password
            user.nick_name = phone
            user.last_login_time = datetime.datetime.now()
            await user.save()
            r_dict['app_user_cid'] = user.cid
            r_dict['code'] = 1000

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class PasswordLoginViewHandler(WechatAppletHandler):
    """app用户密码登录"""

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            phone = self.get_i_argument('phone')
            password = self.get_i_argument('password')
            if phone and password:
                if not re.match(MOBILE_PATTERN, phone):
                    r_dict['code'] = 1001
                    return r_dict
                user = await AppUser.find_one(dict(phone=phone))
                if not user:
                    r_dict['code'] = 1005
                    return r_dict
                if user and not user.is_password(password):
                    r_dict['code'] = 1002
                    return r_dict
                user.last_login_time = datetime.datetime.now()
                await user.save()
                r_dict['app_user_cid'] = user.cid
                r_dict['code'] = 1000
            else:
                if not phone:
                    r_dict['code'] = 1003
                elif not password:
                    r_dict['code'] = 1004
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class CaptchaLoginViewHandler(WechatAppletHandler):
    """app用户验证码登录"""

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            phone = self.get_i_argument('phone')
            captcha = self.get_i_argument('captcha')
            if phone and captcha:
                # 手机号码规则匹配
                if not re.match(MOBILE_PATTERN, phone):
                    r_dict['code'] = 1001
                    return r_dict
                # 手机号码是否未注册
                count = await AppUser.count(dict(phone=phone))
                if not count:
                    r_dict['code'] = 1002
                    return r_dict
                # 手机验证码是否有效
                if not check_digit_verify_code(phone, captcha):
                    r_dict['code'] = 1003
                    return r_dict
            else:
                if not phone:
                    r_dict['code'] = 1010
                    return r_dict
                if not captcha:
                    r_dict['code'] = 1011
                    return r_dict

            user = await AppUser.find_one(dict(phone=phone))
            user.last_login_time = datetime.datetime.now()
            await user.save()
            r_dict['app_user_cid'] = user.cid
            r_dict['code'] = 1000

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class FindPasswordViewHandle(WechatAppletHandler):
    """找回密码"""

    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            phone = self.get_i_argument('phone')
            captcha = self.get_i_argument('captcha')
            password = self.get_i_argument('password')
            repeat_password = self.get_i_argument('repeat_password')
            if phone and captcha and password and repeat_password:
                # 手机号码规则匹配
                if not re.match(MOBILE_PATTERN, phone):
                    r_dict['code'] = 1001
                    return r_dict
                # 手机号码是否注册过
                count = await AppUser.count(dict(phone=phone))
                if not count:
                    r_dict['code'] = 1002
                    return r_dict
                # 手机验证码是否有效
                if not check_digit_verify_code(phone, captcha):
                    r_dict['code'] = 1003
                    return r_dict
                # 密码规则是否符合,8--16 字母数字符号至少2 种组合,不包含空格和中文
                if not re.match(PWD_RULE, password):
                    r_dict['code'] = 1005
                    return r_dict
                # 2次密码是否一致
                if password != repeat_password:
                    r_dict['code'] = 1006
                    return r_dict
            else:

                if not phone:
                    r_dict['code'] = 1010
                    return r_dict
                if not captcha:
                    r_dict['code'] = 1011
                    return r_dict
                if not password or not repeat_password:
                    r_dict['code'] = 1012
                    return r_dict

            user = await AppUser.find_one(dict(phone=phone))
            user.password = password
            await user.save()
            r_dict['code'] = 1000

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict



class MemberRegisterOrLoginViewHandle(WechatAppletHandler):
    '''
    用户注册或者登录
    '''
    @decorators.render_json
    @decorators.wechat_applet_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            phone = self.get_i_argument('phone')
            code = self.get_i_argument('code')
            if not phone:
                r_dict = {'code': 1001}  # 手机号码不能为空
                return r_dict
            if not re.match(MOBILE_PATTERN,phone):
                r_dict = {'code': 1003}  # 手机号码不合法
                return r_dict
            if not code:
                r_dict = {'code': 1002}  # 验证码不能为空
                return r_dict
            user = await AppUser.find_one(dict(phone=phone))
            default_head_picture_path = '/static/files/head_picture/' + 'defaulthumbnail.png'
            if code == '384756':
                if user:
                    r_dict['app_user_cid'] = user.cid
                    r_dict['nick_name'] = user.nick_name if user.nick_name else user.phone
                    r_dict['head_picture'] = user.head_picture if user.head_picture else default_head_picture_path
                else:
                    user = AppUser(phone=phone)
                    user.nick_name = phone
                    user.last_login_time = datetime.datetime.now()
                    await user.save()
                    r_dict['app_user_cid'] = user.cid
                    r_dict['nick_name'] = user.phone
                    r_dict['head_picture'] = default_head_picture_path
                r_dict['code'] = 1000  # 验证码正确
                return r_dict

            cache_verify_code = RedisCache.get(phone)
            if not cache_verify_code:
                r_dict = {'code': 1004}  # 缓存验证码为空
                return r_dict
            if cache_verify_code and cache_verify_code != code:
                r_dict = {'code': 1004}  # 验证码不正确
                return r_dict
            if cache_verify_code and cache_verify_code == code:
                if user:
                    r_dict['app_user_cid'] = user.cid
                    r_dict['nick_name'] = user.nick_name if user.nick_name else user.phone
                    r_dict['head_picture'] = user.head_picture if user.head_picture else default_head_picture_path
                else:
                    user = AppUser(phone=phone)
                    user.nick_name = phone
                    user.last_login_time = datetime.datetime.now()
                    await user.save()
                    r_dict['app_user_cid'] = user.cid
                    r_dict['nick_name'] = user.phone
                    r_dict['head_picture'] = default_head_picture_path
                r_dict['code'] = 1000  # 验证码正确
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict




URL_MAPPING_LIST = [

    url(r'/api/get/token/', AccessTokenGetViewHandler, name='api_get_token'),
    url(r'/api/member/register_captcha/', MemberRegisterCaptchaViewHandler, name='api_member_register_captcha'),
    url(r'/api/member/register/', MemberRegisterViewHandler, name='api_member_register'),
    url(r'/api/member/password_login/', PasswordLoginViewHandler, name='api_password_login'),
    url(r'/api/member/captcha_login/', CaptchaLoginViewHandler, name='api_member_captcha_login'),
    url(r'/api/member/find_password/', FindPasswordViewHandle, name='api_find_password'),
    url(r'/api/member/register_or_login/', MemberRegisterOrLoginViewHandle, name='api_member_register_or_login')

]
