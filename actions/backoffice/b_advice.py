import traceback
import datetime

from bson import ObjectId
from pymongo import UpdateOne
from tornado.web import url

from commons.common_utils import get_increase_code
from commons.page_utils import Paging
from db import STATUS_FEEDBACK_CATEGORY_PUBLIC
from db.models import HelpFeedback
from enums import PERMISSION_TYPE_USER_MANAGEMENT
from web import BaseHandler, decorators
from logger import log_utils
logger = log_utils.get_logging()


class AdviceListViewHandler(BaseHandler):
    """
    反馈建议列表
    """
    @decorators.render_template('backoffice/advice/list_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        advice_category = self.get_argument('advice_category', '')
        query_params = {'record_flag': 1}
        lang = self.get_argument('lang', '')
        if lang == 'en':
            lang = 'en'
        else:
            lang = 'cn'
        query_param = {}
        and_query_param = [{'record_flag': 1}]
        if advice_category:
            and_query_param.append({'category':  int(advice_category)})
        if and_query_param:
            query_param['$and'] = and_query_param
        # 分页 START
        per_page_quantity = int(self.get_argument('per_page_quantity', 10))
        to_page_num = int(self.get_argument('page', 1))
        page_url = '%s?page=$page&per_page_quantity=%s&lang=%s' % (self.reverse_url("backoffice_advice_list"),
                                                                   per_page_quantity, lang)
        paging = Paging(page_url, HelpFeedback, current_page=to_page_num, items_per_page=per_page_quantity,
                        sort=['-updated_dt'], **query_param)
        await paging.pager()
        # 分页 END

        return locals()


class AdviceAddViewHandler(BaseHandler):
    """
        新增公共反馈
    """

    @decorators.render_template('backoffice/advice/add_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        return locals()

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = dict(code=0)

        advice_content = self.get_argument('advice_content')
        advice_feedback = self.get_argument('advice_feedback')

        status = self.get_argument('status')
        if advice_content and advice_feedback  and status:

            advice = HelpFeedback()
            advice.category=STATUS_FEEDBACK_CATEGORY_PUBLIC
            advice.content = advice_content
            advice.question_time = datetime.datetime.now()
            advice.feedback = advice_feedback
            advice.answer_time = datetime.datetime.now()
            advice.status = status
            advice = await advice.save()
            res['code'] = 1
            res['manager_id'] = advice
        else:
            res['code'] = -2
        return res


class AdviceEditViewHandler(BaseHandler):
    """
    回复编辑建议反馈
    """

    @decorators.render_template('backoffice/advice/edit_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        advice_info = self.get_argument('manager_id')
        advice = await HelpFeedback.get_by_id(advice_info)
        return {'manager': advice, 'manager_id': advice_info}

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = dict(code=0)
        manager_id = self.get_argument('manager_id')
        advice_content = self.get_argument('advice_content')
        advice_feedback = self.get_argument('advice_feedback')

        status = self.get_argument('status')
        if advice_content and advice_feedback and status:
            advice = await HelpFeedback().get_by_id(manager_id)
            advice.content = advice_content
            advice.feedback = advice_feedback
            advice.answer_time = datetime.datetime.now()
            advice.status = status
            advice.updated_dt = datetime.datetime.now()
            advice.updated_id = self.current_user.oid
            advice = await advice.save()
            res['code'] = 1
            res['manager_id'] = advice
        else:
            res['code'] = -2
        return res

class AdviceDeleteViewHandler(BaseHandler):
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
                await HelpFeedback.delete_by_ids(data)
                res['code'] = 1
            except Exception:
                logger.error(traceback.format_exc())
            return res
        else:
            res['code'] = -1
            return res



class AdviceStatusViewHandler(BaseHandler):
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
                                                               'updated_dt': datetime.datetime.now(),
                                                               'updated_id': self.current_user.oid}}))
                if update_requests:
                    modified_count = await HelpFeedback.update_many(update_requests)
                    res['code'] = 1
                    res['modified_count'] = modified_count
            except Exception:
                logger.error(traceback.format_exc())
        return res



URL_MAPPING_LIST = [
    url(r'/backoffice/advice/list/', AdviceListViewHandler, name='backoffice_advice_list'),
    url(r'/backoffice/advice/add/', AdviceAddViewHandler, name='backoffice_advice_add'),
    url(r'/backoffice/advice/edit/', AdviceEditViewHandler, name='backoffice_advice_edit'),
    url(r'/backoffice/advice/delete/', AdviceDeleteViewHandler, name='backoffice_advice_delete'),
    url(r'/backoffice/advice/status/', AdviceStatusViewHandler, name='backoffice_advice_status'),

]