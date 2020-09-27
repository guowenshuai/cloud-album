# !/usr/bin/python
# -*- coding:utf-8 -*-
import datetime
import asyncio

from commons import common_utils
from commons.aes_utils import AESCipher
from commons.common_utils import md5
from commons.rsa_utils import RsaCipher
from db import STATUS_USER_ACTIVE, models, STATUS_NOT_FORCE_UPDATE, STATUS_LATEST_VERSION, STATUS_UNPUBLISHED_VERSION, \
    STATUS_ALBUM_TYPE_VIDEO
from db.models import User, AppVersion, HelpFeedback, PhotoAlbum, AppUser, File
from enums import ALL_PERMISSION_TYPE_LIST, KEY_INCREASE_USER
from motorengine import DocumentMetaclass
from motorengine.stages import MatchStage


async def init_indexes():
    """
    初始化索引
    :return:
    """
    model_list = []
    attributes = vars(models)
    if attributes:
        for name, attribute in attributes.items():
            if name not in ['SyncDocument', 'AsyncDocument', 'Document', 'BaseModel'] \
                    and attribute.__class__ == DocumentMetaclass:
                model_list.append((name, attribute))

    if model_list:
        for name, model in model_list:
            result = await model.create_indexes()
            if result:
                print('Model [%s] indexes create succeed!' % name)


async def init_users():
    """
    初始化用户信息
    :return:
    """

    user = await User.find_one(dict(login_name='admin'))
    if user:
        await user.delete()

    user = User()
    user.code = common_utils.get_increase_code(KEY_INCREASE_USER)
    user.name = '超级管理员'
    user.email = '943738808@qq.com'  # 邮箱
    user.mobile = '15106139173'  # 手机
    user.superuser = True  # 是否为超管
    user.login_name = 'admin'  # 用户名
    user.login_password = md5('123456')  # 密码
    user.status = STATUS_USER_ACTIVE  # 状态
    user.content = '超级管理员，无所不能'  # 备注
    user.permission_code_list = ALL_PERMISSION_TYPE_LIST

    oid = await user.save()
    if oid:
        print('Initialize user [', user.name, '] succeed!')


async def init_appversion():
    """
    初始化用户信息
    :return:
    """



    version = AppVersion()
    version.version = '1.0.0'
    version.update_content = '超级管理员'
    version.link = '943738808@qq.com'  # 邮箱
    version.is_force_update = STATUS_NOT_FORCE_UPDATE  # 手机
    version.is_latest_version = STATUS_LATEST_VERSION  # 是否为超管
    version.status = STATUS_UNPUBLISHED_VERSION  # 用户名



    oid = await version.save()
    if oid:
        print('Initialize user [', version.version, '] succeed!')


async def init_advice():
    """
    初始化用户信息
    :return:
    """
    advice = HelpFeedback()
    advice.category = 2
    advice.app_user_cid = '021FDCEC96569C5EC9C56ED6E51E9385'
    advice.content = '炒币能赚钱吗'
    advice.question_time =datetime.datetime.now()
    advice.answer_time =datetime.datetime.now()
    advice.end_time =datetime.datetime.now()
    advice.feedback = '赚钱'
    advice.status = 0



    oid = await advice.save()
    if oid:
        print('Initialize user [', advice.content, '] succeed!')


async def init_add_user():
    """
    批量增加用户
    :return:
    """
    rsa_cipher = RsaCipher()
    pubkey, privkey = rsa_cipher.new()
    privkey = rsa_cipher.dumps(privkey)
    pubkey = rsa_cipher.dumps(pubkey)

    phone = 17621890001
    for i in range(12000):
        phone = int(phone)
        phone+=1
        phone = str(phone)
        password = md5('12345678')
        pw_md5 = md5(password)
        aes = AESCipher(pw_md5)
        enc_priv = aes.encrypt(privkey)
        user = AppUser(phone=phone)
        user.password = password
        user.pwd_private_key = enc_priv.decode()
        user.public_key = pubkey.decode()
        user.last_login_time = datetime.datetime.now()
        oid = await user.save()
        # 创建图片默认相册
        album = PhotoAlbum(app_user_cid=user.cid)
        await album.save()

        # 创建视频默认相册
        album = PhotoAlbum(app_user_cid=user.cid, album_type=STATUS_ALBUM_TYPE_VIDEO)
        await album.save()

        if oid:
            print('Initialize user [', user.phone, '] succeed!')


async def init_add_album():
    """
    批量增加用户相册
    :return:
    """
    phone_list = await AppUser.find().to_list(None)
    for i in phone_list:
        # 创建图片默认相册
        album1 = PhotoAlbum(app_user_cid=i.cid, name='test1'+ i.phone)
        oid1 = await album1.save()
        album2 = PhotoAlbum(app_user_cid=i.cid, name='test2' + i.phone)
        oid2 = await album2.save()
        if oid1 and oid2:
            print('Initialize user [', album1.name, album2.name,'] succeed!')


async def init_add_file():
    """
    批量增加用户相册文件
    :return:
    """
    filter_stage = dict(album_type=1)
    match = MatchStage(filter_stage)
    album_list = await PhotoAlbum.aggregate([match]).to_list(None)
    for i in album_list:
        # 添加图片到所有相册
        for j,s in enumerate(album_list,start=1):
            file_data = File(photo_album_cid=i.cid, hash=s,app_user_cid=i.app_user_cid,name=str(j),size=j)
            oid = await file_data.save()
            if oid:
                print('Initialize user [', file_data.name,'] succeed!')
task_list = [
    init_indexes(),
    init_users(),
    # init_appversion(),
    # init_advice(),
    # init_add_user(),
    # init_add_album(),
    # init_add_file(),
]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(task_list))
loop.close()
