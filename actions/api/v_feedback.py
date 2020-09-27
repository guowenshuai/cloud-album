import traceback
import datetime

from commons.common_utils import datetime2str
from tornado.web import url
from db.models import HelpFeedback, Agreement
from db.enums import STATUS_FEEDBACK_CATEGORY_PERSONAL, STATUS_FEEDBACK_CATEGORY_PUBLIC, STATUS_FEEDBACK_EFFECTIVE
from web import WechatAppletHandler, decorators
from logger import log_utils

logger = log_utils.get_logging()


class FeedbackViewHandler(WechatAppletHandler):
    """
    获取公共问题与答案
    """

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            advice = await HelpFeedback.find(dict(category=STATUS_FEEDBACK_CATEGORY_PUBLIC,
                                                  status=STATUS_FEEDBACK_EFFECTIVE)).to_list(None)
            info = []
            for i in advice:
                info.append({'question': i.content, 'answer': i.feedback,
                             'time': datetime2str(i.answer_time, date_format='%Y-%m-%d')})
            r_dict = {'code': 1000, 'info': info}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class UserFeedbackViewHandler(WechatAppletHandler):
    """
    获取用户个人问题与回复
    """

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            advice = await HelpFeedback.find(
                dict(app_user_cid=self.current_user.cid, category=STATUS_FEEDBACK_CATEGORY_PERSONAL)).to_list(None)
            info = []
            for i in advice:
                info.append({'question': i.content, 'answer': i.feedback,
                             'time': datetime2str(i.answer_time, date_format='%Y-%m-%d')})
            r_dict = {'code': 1000, 'info': info}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class UserFeedbackAddHandler(WechatAppletHandler):
    """
    用户提出意见
    """

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        r_dict = {'code': 0}
        try:
            category = STATUS_FEEDBACK_CATEGORY_PERSONAL
            app_user_cid = self.get_i_argument('app_user_cid')
            content = self.get_i_argument('content')
            question_time = datetime.datetime.now()
            if app_user_cid and content:
                advice = HelpFeedback(category=category, app_user_cid=app_user_cid,
                                      content=content, question_time=question_time)
                await advice.save()
                r_dict['code'] = 1000

        except Exception:
            logger.error(traceback.format_exc())
        return r_dict

class AgreementHandler(WechatAppletHandler):
    """
    用户协议
    """
    @decorators.render_json
    async def get(self, *args, **kwargs):
        r_dict={'code':0}
        category = int(self.get_argument('category'))
        try:
            agreement = await Agreement.find(dict(category=category)).sort('created_dt',-1).limit(1).to_list(None)
            if agreement:
                r_dict={'code':1000,'info':agreement[0]}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict



URL_MAPPING_LIST = [
    url(r'/api/feedback/list/', FeedbackViewHandler, name='api_feedback_list'),
    url(r'/api/feedback/userlist/', UserFeedbackViewHandler, name='api_feedback_userlist'),
    url(r'/api/feedback/add/', UserFeedbackAddHandler, name='api_feedback_add'),
    url(r'/api/agreement/one/', AgreementHandler, name='api_agreement'),
]
