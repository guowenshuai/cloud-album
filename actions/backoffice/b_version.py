# !/usr/bin/python
# -*- coding:utf-8 -*-

import traceback
from datetime import datetime

from bson import ObjectId
from pymongo import UpdateOne
from tornado.web import url

from commons.common_utils import get_increase_code
from commons.page_utils import Paging
from db.models import AppVersion, Role
from enums import PERMISSION_TYPE_USER_MANAGEMENT
from web import BaseHandler, decorators
from logger import log_utils
logger = log_utils.get_logging()

class VersionListViewHandler(BaseHandler):
    """
    版本列表
    """
    @decorators.render_template('backoffice/version/list_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        search_version = self.get_argument('search_version', '')
        query_params = {'record_flag': 1}
        lang = self.get_argument('lang', '')
        if lang == 'en':
            lang = 'en'
        else:
            lang = 'cn'
        query_param = {}
        and_query_param = [{'record_flag': 1}]
        if search_version:
            and_query_param.append({'version': {'$regex': search_version}})
        if and_query_param:
            query_param['$and'] = and_query_param
        # 分页 START
        per_page_quantity = int(self.get_argument('per_page_quantity', 10))
        to_page_num = int(self.get_argument('page', 1))
        page_url = '%s?page=$page&per_page_quantity=%s&lang=%s' % (self.reverse_url("backoffice_version_list"),
                                                                   per_page_quantity, lang)
        paging = Paging(page_url, AppVersion, current_page=to_page_num, items_per_page=per_page_quantity,
                        sort=['-updated_dt'], **query_param)
        await paging.pager()
        # 分页 END

        return locals()



class VersionAddViewHandler(BaseHandler):
    """
    新增版本
    """

    @decorators.render_template('backoffice/version/add_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        return locals()

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = dict(code=0)

        version_num = self.get_argument('version_num')
        version_content = self.get_argument('version_content')
        version_link = self.get_argument('version_link')
        force_update = self.get_argument('force_update')
        laster_version = self.get_argument('laster_version')
        status = self.get_argument('status')
        if version_num and version_content and version_link and force_update and laster_version and status:
            # 校验版本号
            exist_count = await AppVersion.count(dict(version=version_num))
            if exist_count:
                res['code'] = -1
            else:
                version = AppVersion()
                version.version = version_num
                version.update_content = version_content
                version.link = version_link
                version.is_force_update = force_update
                version.is_latest_version = laster_version
                version.status = status
                version = await version.save()
                res['code'] = 1
                res['manager_id'] = version
        else:
            res['code'] = -2
        return res


class VersionEditViewHandler(BaseHandler):
    """
    编辑版本
    """

    @decorators.render_template('backoffice/version/edit_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        version_info = self.get_argument('manager_id')
        version = await AppVersion.get_by_id(version_info)

        return {'manager': version, 'manager_id': version_info}

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = dict(code=0)
        version_id = self.get_argument('manager_id', '')
        version_num = self.get_argument('version_num')
        version_content = self.get_argument('version_content')
        version_link = self.get_argument('version_link')
        force_update = self.get_argument('force_update')
        laster_version = self.get_argument('laster_version')
        status = self.get_argument('status')
        if version_num and version_content and version_link and force_update and laster_version and status and version_id:
            # 校验版本号
            version = await AppVersion.get_by_id(version_id)
            version.version = version_num
            version.update_content = version_content
            version.link = version_link
            version.is_force_update = force_update
            version.is_latest_version = laster_version
            version.status = status
            version.updated_dt = datetime.now()
            version.updated_id = self.current_user.oid
            await version.save()
            res['code'] = 1
        else:
            res['code'] = -3
        return res


class VersionDeleteViewHandler(BaseHandler):
        """
        删除版本
        """
        @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
        @decorators.render_json
        async def post(self):
            res = {'code': 0}
            data = self.get_arguments('manager_id[]')
            if data:

                try:
                    await AppVersion.delete_by_ids(data)
                    res['code'] = 1
                except Exception:
                    logger.error(traceback.format_exc())
                return res
            else:
                res['code'] = -1
                return res


class VerionStatusViewHandler(BaseHandler):
    """
    修改版本状态
    """

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = {'code': 0}
        user_ids = self.get_arguments('manager_id[]')
        target_status = self.get_argument('target_status')
        if user_ids and target_status:
            try:
                update_requests = []
                for user_id in user_ids:
                    update_requests.append(UpdateOne({'_id': ObjectId(user_id)},
                                                     {'$set': {'status': int(target_status),
                                                               'updated_dt': datetime.now(),
                                                               'updated_id': self.current_user.oid}}))
                if update_requests:
                    modified_count = await AppVersion.update_many(update_requests)
                    res['code'] = 1
                    res['modified_count'] = modified_count
            except Exception:
                logger.error(traceback.format_exc())
        return res


URL_MAPPING_LIST = [
    url(r'/backoffice/version/list/', VersionListViewHandler, name='backoffice_version_list'),
    url(r'/backoffice/version/add/', VersionAddViewHandler, name='backoffice_version_add'),
    url(r'/backoffice/version/edit/', VersionEditViewHandler, name='backoffice_version_edit'),
    url(r'/backoffice/version/delete/', VersionDeleteViewHandler, name='backoffice_version_delete'),
    url(r'/backoffice/version/status/', VerionStatusViewHandler, name='backoffice_version_status'),
]
