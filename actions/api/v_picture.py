import traceback
from tornado.web import url
from db import STATUS_FILE_UPLOAD_TYPE_PIC, STATUS_FILE_EFFECFIVE
from db.models import File, Task, PhotoAlbum
from web import WechatAppletHandler, decorators
from logger import log_utils
from datetime import datetime
from motorengine.stages import MatchStage, GroupStage, ProjectStage, SortStage
from commons.file_utils import upload_file_to_ipfs
import settings

logger = log_utils.get_logging()


class PictureUploadViewHandler(WechatAppletHandler):
    '''
    图片上传到ipfs
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            print(self.current_user.cid)
            album_cid = self.get_i_argument('album_cid')
            app_user_cid = self.current_user.cid
            if not album_cid:
                r_dict['code'] = 1002
                return r_dict
            num = int(self.get_i_argument('num', 0))
            if num:
                for i in range(num):
                    file_list = self.request.files.get('file' + str(i))
                    if file_list:
                        file = file_list[0]
                        task = Task(app_user_cid=app_user_cid, size=0, start_time=datetime.now())
                        await task.save()
                        upload_file_to_ipfs(album_cid, app_user_cid, file, task.cid, STATUS_FILE_UPLOAD_TYPE_PIC)
                r_dict['code'] = 1000
            else:
                r_dict['code'] = 1003

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class PictureAllViewHandler(WechatAppletHandler):
    '''
    显示全部图片
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            base_url = settings.BASE_URL
            app_user_cid = self.current_user.cid
            filter_dict = dict(category=STATUS_FILE_UPLOAD_TYPE_PIC,
                               status=STATUS_FILE_EFFECFIVE,
                               app_user_cid=app_user_cid)
            match = MatchStage(filter_dict)
            group = GroupStage(
                {"$dateToString": {'format': '%Y-%m-%d', 'date': '$created_dt'}},
                day_picture_list={'$push': {'hash': '$hash', 'cid': '$cid',
                                            'name': '$name', 'size': '$size',
                                            'created_dt': '$created_dt',
                                            'thumbnail': '$thumbnail',
                                            'url': {'$concat': [base_url, '$hash']}}}
            )  
            sort1 = SortStage([('created_dt', -1)])
            sort2 = SortStage([('_id', -1)])
            project = ProjectStage(day='$_id', _id=0, day_picture_list=1)
            picture_list = await File.aggregate([match, sort1, group, sort2, project]).to_list(None)
            new_picture_list = []
            for picture in picture_list:
                new_picture_list.append({'day': picture.day, 'day_picture_list': picture.day_picture_list})
            r_dict['list'] = new_picture_list
            r_dict['code'] = 1000
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class PictureAlbumList(WechatAppletHandler):
    '''
    指定相册图片列表
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        指定相册全部图片显示
        :param args:
        :param kwargs:
        :return: name;count;cid;urlpic;
        '''
        r_dict = {'code': 0}
        try:
            base_url = settings.BASE_URL
            album_cid = self.get_i_argument('album_cid')
            album = await PhotoAlbum.find_one(dict(cid=album_cid))
            if not album:
                r_dict = {'code': 1002}  # 相册编号为空或者无效
                return r_dict
            filter_dict = dict(photo_album_cid=album_cid,
                               status=STATUS_FILE_EFFECFIVE,
                               category=STATUS_FILE_UPLOAD_TYPE_PIC)
            match = MatchStage(filter_dict)
            sort1 = SortStage([('created_dt', -1)])
            picture_list = await File.aggregate([match, sort1]).to_list(None)
            picture_data_list = []
            for i in picture_list:
                picture_data_list.append({'cid': i.cid, 'hash': i.hash,
                                          'url': base_url + i.hash, 'thumbnail': i.thumbnail})
            r_dict = {'code': 1000, 'name': album.name, 'count': len(picture_list), 'list': picture_data_list}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


URL_MAPPING_LIST = [
    url(r'/api/picture/upload/', PictureUploadViewHandler, name='api_picture_upload'),
    url(r'/api/picture/all/', PictureAllViewHandler, name='api_picture_all'),
    url(r'/api/picture/album/list/', PictureAlbumList, name='api_picture_album_list'),
]
