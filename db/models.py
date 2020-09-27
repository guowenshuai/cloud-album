# !/usr/bin/python
# -*- coding:utf-8 -*-
from datetime import datetime

from commons.common_utils import md5
from commons.decorators import lazy_property
from db.enums import *
from motorengine import DESC
from motorengine.document import AsyncDocument, SyncDocument
from motorengine.fields import IntegerField, StringField, DateTimeField, ListField, BooleanField, DictField, FloatField


class BaseModel(AsyncDocument, SyncDocument):
    """
    基础模型
    """
    created_id = StringField()  # 创建_id
    created_dt = DateTimeField(default=datetime.now)  # 创建时间
    updated_id = StringField()  # 更新_id
    updated_dt = DateTimeField(default=datetime.now)  # 更新时间
    record_flag = IntegerField(default=1)  # 记录标记, 0: 无效的, 1: 有效的
    needless = DictField(default={})  # 冗余字段

    # 索引
    _indexes = [('created_dt', DESC), ('updated_dt', DESC), 'record_flag']


class InstantMail(BaseModel):
    mail_server = DictField(required=True)  # 邮件配置
    mail_from = StringField(required=True)  # 发件人
    mail_to = ListField(required=True)  # 收件人
    post_dt = DateTimeField(default=datetime.now)  # 邮件发送时间
    status = IntegerField(required=True)  # 状态
    subject = StringField(default='')  # 主题
    content = StringField(default='')  # 内容
    content_images = DictField(default={})  # 图片资源
    attachments = ListField(default=[])  # 附件

    exception = StringField()  # 异常信息

    _indexes = ['mail_from', 'mail_to', 'status', 'subject']


class InstantSms(BaseModel):
    sms_server = StringField(required=True)  # 短信服务
    account = StringField(required=True)  # 账号
    post_dt = DateTimeField(default=datetime.now)  # 发送时间
    status = IntegerField(required=True)  # 状态
    mobile = StringField(default='')  # 手机号
    content = StringField(default='')  # 内容

    exception = StringField()  # 异常信息

    _indexes = ['sms_server', 'account', 'status', 'post_dt', 'mobile']


class AdministrativeDivision(BaseModel):
    """
    行政区划
    """
    code = StringField(db_field='post_code', required=True)  # 区划编号（邮编）
    parent_code = StringField(default=None)  # 父级区划编号
    title = StringField(required=True)  # 区划名
    en_title = StringField()  # 区划英文名
    level = StringField()  # 所属行政级别（P：省，C：市，D：区、县）

    @lazy_property
    async def parent(self):
        """
        父级行政区划
        :return:
        """
        if self.parent_code:
            return await AdministrativeDivision.find_one(dict(code=self.parent_code))
        return None

    async def children(self, filter_code_list=None):
        """
        筛选子一级行政区划
        :param filter_code_list: 筛选的子集code
        :return:
        """
        if filter_code_list:
            if not isinstance(filter_code_list, list):
                raise ValueError('"filter_code_list" must be a tuple or list.')
        match = {
            'parent_code': self.code
        }
        if filter_code_list:
            match['code'] = {'$in': filter_code_list}
        return await AdministrativeDivision.find(match).to_list(None)

    # 索引
    _indexes = ['code', 'parent_code', 'title', 'en_title', 'level']


class UploadFiles(BaseModel):
    code = StringField(required=True, max_length=64)  # 文件编号
    title = StringField(required=True, max_length=64)  # 文件名
    source_title = StringField(required=True, max_length=256)  # 源标题
    category = IntegerField(default=CATEGORY_UPLOAD_FILE_OTHER, choice=CATEGORY_UPLOAD_FILE_LIST)  # 类别
    content_type = StringField()  # 附件类型
    size = IntegerField(required=True)  # 文件大小

    _indexes = ['code', 'category', 'size']


class User(BaseModel):
    """
    用户
    """
    code = StringField()  # 用户编号
    name = StringField()  # 用户姓名
    sex = IntegerField(choice=SEX_LIST)  # 性别
    email = StringField()  # 电子邮箱
    mobile = StringField(max_length=24)  # 手机号
    phone = StringField(max_length=24)  # 固话
    status = IntegerField(default=STATUS_USER_ACTIVE, choice=STATUS_USER_LIST)  # 状态
    content = StringField()  # 备注
    superuser = BooleanField(default=False)  # 是否超管

    login_name = StringField(required=True, max_length=64)  # 登录名
    login_password = StringField(required=True, max_length=32)  # 登录密码
    login_times = IntegerField(default=0)  # 登录次数
    login_datetime = DateTimeField(default=datetime.now)  # 最近登录时间
    access_secret_id = StringField(max_length=32)  # Access Secret ID
    access_secret_key = StringField(max_length=128)  # Access Secret KEY

    permission_code_list = ListField(default=[])  # 拥有的权限
    role_code_list = ListField(default=[])  # 所属的角色

    manage_region_code_list = ListField(default=[])  # 可管理的地区
    city = StringField()  # 城市标题
    province = StringField()  # 省份标题
    __lazy_all_permission_code_list = None
    __lazy_role_list = None

    def has_perm_sync(self, perm_code):
        """
        判断是否有对应的权限(同步的)
        :param perm_code: 权限编码或编码LIST或编码TUPLES
        :return: True or False
        """
        if perm_code:
            if self.superuser:
                return True
            if isinstance(perm_code, (tuple, list)):
                code_list = perm_code
            else:
                code_list = [perm_code]
            for code in code_list:
                all_permission_codes = self.__lazy_all_permission_code_list
                perm = self.superuser or (all_permission_codes and code in all_permission_codes)
                if perm:
                    return True
        return False

    async def has_perm(self, perm_code):
        """
        判断是否有对应的权限
        :param perm_code: 权限编码或编码LIST或编码TUPLES
        :return: True or False
        """
        if perm_code:
            if self.superuser:
                return True
            if isinstance(perm_code, (tuple, list)):
                code_list = perm_code
            else:
                code_list = [perm_code]
            for code in code_list:
                all_permission_codes = await self.all_permission_codes()
                perm = self.superuser or (all_permission_codes and code in all_permission_codes)
                if perm:
                    return True
        return False

    async def all_permission_codes(self):
        """
        用户所有权限编号
        :return:
        """
        if self.__lazy_all_permission_code_list is not None:
            return self.__lazy_all_permission_code_list
        self.__lazy_all_permission_code_list = []
        if self.permission_code_list:
            self.__lazy_all_permission_code_list.extend(self.permission_code_list)
        role_list = await self.roles_list()
        if role_list:
            for role in role_list:
                if role and role.permission_code_list:
                    self.__lazy_all_permission_code_list.extend(role.permission_code_list)
        return self.__lazy_all_permission_code_list

    async def roles_list(self):
        """
        所属所有角色
        :return:
        """
        if self.__lazy_role_list is not None:
            return self.__lazy_role_list
        self.__lazy_role_list = await Role.find(
            dict(code={'$in': self.role_code_list}, status=STATUS_ROLE_ACTIVE)).to_list(length=None)
        return self.__lazy_role_list

    _indexes = ['code', 'email', 'status', 'login_name', 'login_password', 'access_secret_id',
                'access_secret_key', 'permission_code_list', 'role_code_list']


class Role(BaseModel):
    """
    角色
    """
    code = StringField(required=True)  # 角色编码
    title = StringField(required=True)  # 角色名
    status = IntegerField(default=STATUS_ROLE_ACTIVE, choice=STATUS_ROLE_LIST)  # 状态
    permission_code_list = ListField(default=[])  # 角色权限列表
    content = StringField()  # 备注

    _indexes = ['code', 'status']


class AppUser(BaseModel):
    """
    APP用户表
    """
    phone = StringField(required=True, max_length=24)  # 手机号码
    # __password = StringField()  # 密码
    # pwd_private_key = StringField(required=True)  # 密码与私钥
    # public_key = StringField(required=True)  # 公钥
    nick_name = StringField()  # 昵称
    head_picture = StringField()  # 头像链接
    is_member = IntegerField(default=STATUS_USER_NOT_MEMBER, choice=STATUS_USER_MEMBER_LIST)  # 是否会员
    has_use_space = FloatField(default=0)  # 已使用空间 单位G
    origin_space = FloatField(default=0)  # 初始空间 单位G
    all_space = FloatField(default=0)  # 总空间 单位G
    status = IntegerField(default=STATUS_APP_USER_EFFECTIVE, choice=STATUS_APP_USER_LIST)  # 状态
    is_auto_backup_photo = IntegerField(default=STATUS_USER_AUTO_BACKUP_INACTIVE,
                                        choice=STATUS_USER_AUTO_BACKUP_LIST)  # 是否自动备份照片
    is_auto_backup_video = IntegerField(default=STATUS_USER_AUTO_BACKUP_INACTIVE,
                                        choice=STATUS_USER_AUTO_BACKUP_LIST)  # 是否自动备份视频
    score = IntegerField(default=0)  # 积分
    last_login_time = DateTimeField()  # 上次登录时间

    # @property
    # def password(self):
    #     return self.__password
    #
    # @password.setter
    # def password(self, value):
    #     self.__password = md5(value)
    #
    # def is_password(self, password):
    #     return self.__password == md5(password)

    _indexes = ['phone', 'status']


class MemberType(BaseModel):
    '''
    会员类型表
    '''
    category = IntegerField(default=STATUS_GENERAL_MEMBER, choice=STATUS_MEMBER_TYPE_LIST)
    space_info = StringField()  # 开通空间信息
    time_info = StringField()  # 开通时长信息
    desc = StringField()  # 费用说明
    status = IntegerField(default=STATUS_MEMBER_EFFECTIVE, choice=STATUS_MEMBER_LIST)  # 状态


class MemberInfo(BaseModel):
    '''
    会员信息表
    '''
    app_user_cid = StringField(required=True)  # app用户编号
    member_type_cid = StringField(required=True)  # 会员类型编号
    start_time = DateTimeField(required=True)  # 开通时间
    end_time = DateTimeField(required=True)  # 到期时间
    is_auto_renew = IntegerField(default=STATUS_MEMBER_NOT_AUTO_RENEW, choice=STATUS_MEMBER_AUTO_RENEW_LIST)  # 是否自动续费


class PhotoAlbum(BaseModel):
    '''
    相册表
    '''
    app_user_cid = StringField(required=True)  # app用户编号
    name = StringField(default='default')  # 相册名字
    share_list=ListField()#  分享列表
    link = StringField() #相册链接
    attribute=IntegerField(default=STATUS_ALBUM_ATTR_SELF,choice=STATUS_ALBUM_ATTR_LIST) #相册属性
    pir_key=StringField() #相册公钥
    album_type = IntegerField(default=STATUS_ALBUM_TYPE_PIC, choice=STATUS_ALBUM_TYPE_LIST)
    status = IntegerField(default=STATUS_ALBUM_EFFECTIVE, choice=STATUS_ALBUM_LIST)  # 状态

    _indexes = ['app_user_cid', 'album_type', 'status']


class File(BaseModel):
    '''
    文件对象表
    '''
    photo_album_cid = StringField(required=True)  # 相册编号
    app_user_cid = StringField()  # app用户编号
    category = IntegerField(default=STATUS_FILE_UPLOAD_TYPE_PIC, choice=STATUS_FILE_UPLOAD_TYPE_LIST)  # 类别 图片/ 视频
    size = FloatField()  # 大小
    hash = StringField(required=True)  # 上传成功后返回hash值
    name = StringField()  # 文件名称
    status = IntegerField(default=STATUS_FILE_EFFECFIVE, choice=STATUS_FILE_LIST)  # 状态
    thumbnail = StringField()  # 缩略图

    _indexes = ['photo_album_cid', 'app_user_cid', 'category', 'hash', 'status']


class Task(BaseModel):
    '''
    传输表
    '''
    app_user_cid = StringField(required=True)  # app用户编号
    category = IntegerField(default=STATUS_FILE_TRANSFER_UPLOAD, choice=STATUS_FILE_TRANSFER_LIST)  # 类别 上传/ 下载
    type = IntegerField(default=STATUS_FILE_UPLOAD_TYPE_PIC, choice=STATUS_FILE_UPLOAD_TYPE_LIST)  # 类型 图片/ 视频
    start_time = DateTimeField(required=True)  # 开始时间
    end_time = DateTimeField()  # 结束时间
    size = FloatField(required=True)  # 大小
    status = IntegerField(default=STATUS_TASK_TRANSFER_DOING, choice=STATUS_TASK_TRANSFER_LIST)  # 状态（进行中/已暂停/已完成）
    show_status = IntegerField(default=STATUS_TASK_IS_SHOW, choice=STATUS_TASK_SHOW_LIST)  # 显示状态


class HelpFeedback(BaseModel):
    '''
    帮助反馈表
    '''

    category = IntegerField(default=STATUS_FEEDBACK_CATEGORY_PERSONAL,
                            choice=STATUS_FEEDBACK_CATEGORY_LIST)  # 类别 （个人 / 公共）
    app_user_cid = StringField()  # app用户编号
    content = StringField()  # 问题内容
    question_time = DateTimeField(required=True)  # 问题发布时间
    feedback = StringField()  # 反馈内容
    answer_time = DateTimeField()  # 回答时间
    status = IntegerField(default=STATUS_FEEDBACK_EFFECTIVE, choice=STATUS_FEEDBACK_LIST)  # 状态


class AppVersion(BaseModel):
    '''
    app版本表
    '''
    version = StringField(required=True)  # 版本编号
    update_content = StringField(required=True)  # 更新内容
    link = StringField(required=True)  # 下载链接
    is_force_update = IntegerField(default=STATUS_NOT_FORCE_UPDATE, choice=STATUS_FORCR_UPDATE_LIST)  # 是否需强制更新
    is_latest_version = IntegerField(default=STATUS_PREV_VERSION, choice=STATUS_VERSION_LIST)  # 是否最新版本
    status = IntegerField(default=STATUS_UNPUBLISHED_VERSION, choice=STATUS_PUBLISH_VERSION_LIST)  # 状态

class Agreement(BaseModel):
    category = IntegerField(default=0,choice=[0,1])
    title = StringField(required=True)
    content = StringField(required=True)

class DeviceInfo(BaseModel):
    '''
    设备信息表
    '''
    app_user_cid = StringField(required=True)  # app用户编号
    device_type = StringField(required=True)  # 设备类型
    device_info = StringField(required=True)  # 设备信息
    app_version = StringField(required=True)  # app版本编号
