import traceback
from tornado.web import url
from db import STATUS_FILE_EFFECFIVE, STATUS_FILE_UPLOAD_TYPE_VIDEO
from db.models import File, Task
from web import WechatAppletHandler, decorators
from logger import log_utils
from datetime import datetime
from motorengine.stages import MatchStage, GroupStage, ProjectStage, SortStage
from commons.file_utils import upload_file_to_ipfs
import settings

logger = log_utils.get_logging()


class VideoUploadViewHandler(WechatAppletHandler):
    '''
    视频上传到ipfs
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
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
                        upload_file_to_ipfs(album_cid, app_user_cid, file, task.cid, STATUS_FILE_UPLOAD_TYPE_VIDEO)
                r_dict['code'] = 1000
            else:
                r_dict['code'] = 1003

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class VideoAllViewHandler(WechatAppletHandler):
    '''
    显示全部视频
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            base_url = settings.BASE_URL
            app_user_cid = self.current_user.cid
            filter_dict = dict(category=STATUS_FILE_UPLOAD_TYPE_VIDEO,
                               status=STATUS_FILE_EFFECFIVE,
                               app_user_cid=app_user_cid)
            match = MatchStage(filter_dict)
            group = GroupStage(
                {"$dateToString": {'format': '%Y-%m-%d', 'date': '$created_dt'}},
                day_picture_list={'$push': {'hash': '$hash', 'cid': '$cid',
                                            'name': '$name', 'size': '$size',
                                            'created_dt': '$created_dt',
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


URL_MAPPING_LIST = [
    url(r'/api/video/upload/', VideoUploadViewHandler, name='api_video_upload'),
    url(r'/api/video/all/', VideoAllViewHandler, name='api_video_all'),
]
