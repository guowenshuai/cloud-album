import traceback
import datetime

from bson import ObjectId
from pymongo import UpdateOne
from tornado.web import url

from commons.common_utils import get_increase_code
from commons.page_utils import Paging
from db import STATUS_FEEDBACK_CATEGORY_PUBLIC
from db.models import Agreement
from enums import PERMISSION_TYPE_USER_MANAGEMENT
from web import BaseHandler, decorators
from logger import log_utils
logger = log_utils.get_logging()


class AgreementListViewHandler(BaseHandler):
    """
    反馈建议列表
    """
    @decorators.render_template('backoffice/agreement/list_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        lang = self.get_argument('lang', '')
        if lang == 'en':
            lang = 'en'
        else:
            lang = 'cn'
        # 分页 START
        per_page_quantity = int(self.get_argument('per_page_quantity', 10))
        to_page_num = int(self.get_argument('page', 1))
        page_url = '%s?page=$page&per_page_quantity=%s&lang=%s' % (self.reverse_url("backoffice_agreement_list"),
                                                                   per_page_quantity, lang)
        paging = Paging(page_url, Agreement, current_page=to_page_num, items_per_page=per_page_quantity,
                        sort=['-updated_dt'])
        await paging.pager()
        # 分页 END

        return locals()


class AgreementAddViewHandler(BaseHandler):
    """
        新增用户协议
    """

    @decorators.render_template('backoffice/agreement/add_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        return locals()

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = dict(code=0)

        content = self.get_argument('content')
        title = self.get_argument('title')
        category = self.get_argument('category')
        if content and title:

            agreement = Agreement()
            agreement.title=title
            agreement.category = category
            agreement.content = content
            agreement = await agreement.save()
            res['code'] = 1
            res['manager_id'] = agreement
        else:
            res['code'] = -2
        return res


class AgreementEditViewHandler(BaseHandler):
    """
    修改协议
    """

    @decorators.render_template('backoffice/agreement/edit_view.html')
    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    async def get(self):
        advice_info = self.get_argument('manager_id')
        advice = await Agreement.get_by_id(advice_info)
        return {'manager': advice, 'manager_id': advice_info}

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = dict(code=0)
        manager_id = self.get_argument('manager_id')
        content = self.get_argument('content')
        title = self.get_argument('title')
        category = self.get_argument('category')

        if content and title :
            agreement = await Agreement().get_by_id(manager_id)
            agreement.content = content
            agreement.title = title
            agreement.category = category
            agreement.updated_dt = datetime.datetime.now()
            agreement.updated_id = self.current_user.oid
            agreement = await agreement.save()
            res['code'] = 1
            res['manager_id'] = agreement
        else:
            res['code'] = -2
        return res

class AgreementDeleteViewHandler(BaseHandler):
    """
    删除协议
    """

    @decorators.permission_required(PERMISSION_TYPE_USER_MANAGEMENT)
    @decorators.render_json
    async def post(self):
        res = {'code': 0}
        data = self.get_arguments('manager_id[]')
        if data:
            try:
                await Agreement.delete_by_ids(data)
                res['code'] = 1
            except Exception:
                logger.error(traceback.format_exc())
            return res
        else:
            res['code'] = -1
            return res






URL_MAPPING_LIST = [
    url(r'/backoffice/agreement/list/', AgreementListViewHandler, name='backoffice_agreement_list'),
    url(r'/backoffice/agreement/add/', AgreementAddViewHandler, name='backoffice_agreement_add'),
    url(r'/backoffice/agreement/edit/', AgreementEditViewHandler, name='backoffice_agreement_edit'),
    url(r'/backoffice/agreement/delete/', AgreementDeleteViewHandler, name='backoffice_agreement_delete'),

]