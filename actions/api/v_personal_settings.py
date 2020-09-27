import os
import traceback
from io import BytesIO

from PIL import Image
from tornado.web import url

import settings
from db.models import AppUser
from web import WechatAppletHandler, decorators
from logger import log_utils

logger = log_utils.get_logging()


class UserHeadPictureEditHandler(WechatAppletHandler):
    '''
    修改用户头像
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        修改用户头像
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            pic = self.request.files.get('head_picture')
            if not pic:
                r_dict = {'code': 1002}  # 头像不能为空
                return r_dict
            cid = self.current_user.cid
            user = await AppUser.find_one(dict(cid=cid))
            head_link = self.file_upload_local(cid, pic)
            user.head_picture = head_link
            await user.save()
            head_picture_path = '/static/files/head_picture/' + cid + '.png'
            r_dict['head_picture_path'] = head_picture_path
            r_dict['head_picture_path_humbnail'] = head_link
            r_dict['code'] = 1000
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict

    def file_upload_local(self,app_user_cid, file):
        file_name, file_name_humbnail = str(app_user_cid) + '.png', str(app_user_cid) + 'humbnail' + '.png'
        file_dir = os.path.join(settings.UPLOAD_FILES_PATH, 'head_picture')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        file_path, file_path_humbnail = os.path.join(file_dir, file_name), os.path.join(file_dir, file_name_humbnail)
        image = Image.open(BytesIO(file[0].body))
        image.save(file_path, 'png')
        image = image.resize((128, 128), Image.ANTIALIAS)
        quality_val = 90
        image.save(file_path_humbnail, 'png', quality=quality_val)
        db_path = '/static/files/head_picture/'+ file_name_humbnail
        return db_path


class UserNicknameEditHandler(WechatAppletHandler):
    '''
    修改用户昵称
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        修改用户昵称
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            nick_name = self.get_i_argument('nick_name')
            if not nick_name:
                r_dict = {'code': 1001}  # 昵称不能为空
                return r_dict
            if len(nick_name) > 12:
                r_dict = {'code': 1002}  # 昵称不符合规则
                return r_dict
            user = await AppUser.find_one(dict(cid=self.current_user.cid))
            user.nick_name = nick_name
            await user.save()
            r_dict = {'code': 1000}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


URL_MAPPING_LIST = [
    url(r'/api/user/head_picture/edit/', UserHeadPictureEditHandler, name='/api/user/head_picture/edit/'),
    url(r'/api/user/nick_name/edit/', UserNicknameEditHandler, name='/api/user/nick_name/edit/'),
]
