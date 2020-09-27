import traceback

from tornado.web import url

from commons.common_utils import md5
from db.models import User, AdministrativeDivision
from enums import  \
    KEY_SESSION_USER
from logger import log_utils
from web import decorators, BaseHandler

logger = log_utils.get_logging()


class RaceLoginViewHandler(BaseHandler):
    """
    科协登录页面
    """

    @decorators.render_template('frontsite/auth/login.html')
    async def get(self):
        return locals()

    @decorators.render_json
    async def post(self):
        r_dict = {'code': 0}
        try:
            username = self.get_argument('username', '')
            password = self.get_argument('password', '')
            if username and password:
                user = await User.find_one({'login_name': username})
                if not user:
                    r_dict['code'] = -1  # 没有用户
                    return r_dict

                if md5(password) != user.login_password:
                    r_dict['code'] = -3  # 密码不正确
                    return r_dict
                if not (user.province or user.city):
                    r_dict['code'] = -5
                    return r_dict
                self.session.put(KEY_SESSION_USER, user)
                self.session.save()
                r_dict['code'] = 1
            else:
                r_dict['code'] = -4
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict





class RaceLogoutHandler(BaseHandler):
    async def get(self):
        self.current_user = None
        self.clear_cookie('_xsrf')
        self.session.drop()
        self.redirect(self.reverse_url('frontsite_race_login'))


class RaceSpecialLoginViewHandler(BaseHandler):
    """
    安徽科协账号登录页面
    """

    @decorators.render_template('frontsite/auth/special_login.html')
    async def get(self):
        return locals()

    @decorators.render_json
    async def post(self):
        r_dict = {'code': 0}
        try:
            username = self.get_argument('username', '')
            password = self.get_argument('password', '')
            if username and password:
                user = await User.find_one({'login_name': username})
                if not user:
                    r_dict['code'] = -1  # 没有用户
                    return r_dict

                if md5(password) != user.login_password:
                    r_dict['code'] = -3  # 密码不正确
                    return r_dict
                if not (user.province or user.city):
                    r_dict['code'] = -5
                    return r_dict
                #  可管理地区
                region_code_list = user.manage_region_code_list
                is_enter = False
                for region_code in region_code_list:
                    city_list = await AdministrativeDivision.find({'parent_code': '340000'}).to_list(None)
                    total_code_list = [city.code for city in city_list]
                    total_code_list.append("340000")
                    if region_code in total_code_list:
                        is_enter = True
                if not is_enter:
                    r_dict['code'] = -6
                    return r_dict

                self.session.put(KEY_SESSION_USER, user)
                self.session.save()
                r_dict['code'] = 1
            else:
                r_dict['code'] = -4
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict





URL_MAPPING_LIST = [
    url(r'/frontsite/race/login/', RaceLoginViewHandler, name="frontsite_race_login"),
    url(r'/frontsite/race/login/out/', RaceLogoutHandler, name="frontsite_race_login_out"),
    url(r'/frontsite/race/special/login/', RaceSpecialLoginViewHandler, name="frontsite_race_special_login"),
]
