import datetime
import os
import shutil
import traceback

from pymongo import UpdateOne
from tornado.web import url

import settings
from db.enums import *
from db.models import AppUser, PhotoAlbum, File
from logger import log_utils
from motorengine.stages import MatchStage
from web import WechatAppletHandler, decorators
from shutil import copyfile

logger = log_utils.get_logging()


class AlbumListHandler(WechatAppletHandler):
    '''
    相册视频列表
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        获取相册、视频列表接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            type = self.get_i_argument('type')

            if int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1002}  # 类型为空或不在类型中
                return r_dict
            albums = await PhotoAlbum.find(dict(app_user_cid=self.current_user.cid, album_type=int(type))).to_list(None)
            album_list = []
            for i in albums:
                # album_count = await File.find(dict(photo_album_cid=i.cid, status=STATUS_ALBUM_EFFECTIVE)).to_list(None)
                # album_list.append({'name': i.name, 'count': len(albums), 'cid': i.cid,'link':i.link,'attribute':i.attribute,'pir_key':i.pir_key})
                album_list.append({'name': i.name, 'cid': i.cid, 'attribute': i.attribute,'pir_key':i.pir_key,'link':i.link,'status':i.status})
            r_dict = {'code': 1000, 'list': album_list}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class AlbumCreateHandler(WechatAppletHandler):
    '''
    创建相册、视频接口
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        创建相册、视频接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            name = self.get_i_argument('name')
            type = self.get_i_argument('type')
            if not name:
                r_dict = {'code': 1002}  # 相册名称为空
                return r_dict
            if not type or int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1003}  # 类型为空或不在类型中
                return r_dict
            if await PhotoAlbum.count(dict(app_user_cid=self.current_user.cid, name=name, album_type=int(type))):
                r_dict = {'code': 1004}  # 相册名称不能重复
                return r_dict
            if len(name) >= 25:
                r_dict = {'code': 1005}  # 相册名称规则不匹配
                return r_dict
            album = PhotoAlbum(app_user_cid=self.current_user.cid, name=name, album_type=type)
            await album.save()
            r_dict = {'code': 1000}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class AlbumUplodeHandler(WechatAppletHandler):
    '''
    图片相册文件上传
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        上传相册对象、视频接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            album_file = self.request.files.get('album_file')
            if not album_file:
                r_dict = {'code': 1001}  # 相册名称为空
                return r_dict
            public_key = self.get_i_argument('public_key')
            type = self.get_i_argument('type')
            if int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1002}  # 类型为空或不在类型中
                return r_dict
            mingzi = 'picture' if int(type) == 1 else 'video'
            name = album_file[0]['filename'].split('.')[0]
            msg = await PhotoAlbum.find_one(dict(app_user_cid=self.current_user.cid, album_type=int(type), name=name))
            if msg:
                if msg.link:
                    os.remove(os.path.join(settings.SITE_ROOT, msg.link))
                    logger.info("del album success")
            else:
                new_album = PhotoAlbum(app_user_cid=self.current_user.cid,album_type=int(type),name=name)
                await new_album.save()
            msg = await PhotoAlbum.find_one(dict(app_user_cid=self.current_user.cid, album_type=int(type), name=name))
            logger.info("123")
            file_path = os.path.join(settings.UPLOAD_FILES_PATH, self.current_user.cid, mingzi)
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            logger.info("file_path",file_path)
            full_path = os.path.join(file_path, album_file[0]['filename'].split('.')[0] + "." +
                                     album_file[0]['filename'].split('.')[1])
            logger.info("full_path", full_path)
            with open(full_path, 'wb') as up:
                up.write(album_file[0]['body'])
            up.close()
            logger.info("000000")
            logger.info(full_path,'111111')
            logger.info(os.path.exists(full_path),'eee')
            logger.info("222222")

            for i in msg.share_list:
                info = await PhotoAlbum.find_one(dict(cid=i))
                os.remove(os.path.join(settings.SITE_ROOT, info.link))
                info_path = os.path.join(settings.UPLOAD_FILES_PATH, info.app_user_cid, mingzi)
                full_path = os.path.join(info_path, album_file[0]['filename'].split('.')[0] + "." +
                                         album_file[0]['filename'].split('.')[1])
                with open(full_path, 'wb') as up:
                    up.write(album_file[0]['body'])
                up.close()
                info.link = os.path.join('static', 'files', info.app_user_cid, mingzi, album_file[0]
                ['filename'].split('.')[0] + "." + album_file[0]['filename'].split('.')[1]).replace('\\', '/')
                info.status = msg.status
                info.updated_dt = datetime.datetime.now()
                info.name = album_file[0]['filename'].split('.')[0]
                await info.save()
            msg.link = os.path.join('static', 'files', self.current_user.cid, mingzi, album_file[0]
            ['filename'].split('.')[0] + "." + album_file[0]['filename'].split('.')[1]).replace('\\', '/')
            msg.pir_key = public_key
            await msg.save()
            logger.info("456")
            r_dict = {'code': 1000}
        except Exception:
            logger.info("7890")
            logger.error(traceback.format_exc())
        return r_dict


class AlbumImportHandler1(WechatAppletHandler):
    '''
        图片相册文件导入
        '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        上传相册对象、视频接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            album_name = self.get_i_argument('album_name')
            if not album_name:
                r_dict = {'code': 1003}  # 名称为空
                return r_dict
            public_key = self.get_i_argument('public_key')
            if not public_key:
                r_dict = {'code': 1002}  # 公钥为空
                return r_dict
            type = self.get_i_argument('type')
            if int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1001}  # 类型为空或不在类型中
                return r_dict
            msg = await PhotoAlbum.find_one(
                dict(app_user_cid=self.current_user.cid, album_type=int(type), pir_key=public_key,
                     name=album_name))
            if msg:
                r_dict = {'code': 1005}  # 该相册存在
                return r_dict

            mingzi = 'picture' if int(type) == 1 else 'video'
            info = await PhotoAlbum.find_one(dict(album_type=int(type), pir_key=public_key, name=album_name))
            if info:
                if info.link:
                    file_path = os.path.join(settings.UPLOAD_FILES_PATH, self.current_user.cid, mingzi)
                    if not os.path.exists(file_path):
                        os.makedirs(file_path)
                    msg_info = info.link.split('/')[4].split('.')
                    full_path = os.path.join(file_path, msg_info[0] + '.' + msg_info[1])
                    shutil.copyfile(os.path.join(settings.SITE_ROOT, info.link), full_path)
                    copy_link = os.path.join('static', 'files', self.current_user.cid, mingzi,
                                             msg_info[0] + '.' + msg_info[1]).replace('\\', '/')
                    album = PhotoAlbum(app_user_cid=self.current_user.cid, name=info.name, album_type=info.album_type,
                                       attribute=STATUS_ALBUM_TYPE_SHARE, pir_key=info.pir_key, status=info.status,
                                       link=copy_link)
                    await album.save()
                    info.share_list.append(album.cid)
                    await info.save()
                    r_dict['link'] = "/" + album.link
                    r_dict['code'] = 1000
                else:
                    r_dict = {'code': 1004}
            else:
                r_dict = {'code': 1006}
        except Exception:
            logger.error(traceback.format_exc())

        return r_dict


#j.k
class AlbumImportHandler(WechatAppletHandler):
    '''
        图片相册文件导入
        '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        上传相册对象、视频接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            share_user_cid = self.get_i_argument('share_user_cid')
            album_name = self.get_i_argument('album_name')
            if not album_name:
                r_dict = {'code': 1003}  # 名称为空
                return r_dict
            public_key = self.get_i_argument('public_key')
            if not public_key:
                r_dict = {'code': 1002}  # 公钥为空
                return r_dict
            type = self.get_i_argument('type')
            if int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1001}  # 类型为空或不在类型中
                return r_dict
            user_album = await PhotoAlbum.find_one(
                dict(app_user_cid=self.current_user.cid, album_type=int(type), pir_key=public_key,
                     name=album_name,attribute=2))
            if user_album:
                r_dict = {'code': 1005}  # 该相册重复导入
                return r_dict
            logger.info(public_key)
            share_user_album = await PhotoAlbum.find_one(dict(album_type=int(type), pir_key=public_key, name=album_name,
                                                              app_user_cid=share_user_cid,attribute=1))
            if share_user_album:
                if share_user_album.link:
                    category_dir = "picture" if type==str(STATUS_ALBUM_TYPE_PIC) else "video"
                    split_link = "static/files/"+ share_user_cid + "/" + category_dir + "/"
                    link_txt_name = share_user_album.link.split(split_link)
                    logger.info(link_txt_name)
                    share_user_link = "static/files/"+ self.current_user.cid + "/" + category_dir + "/" + link_txt_name[1]
                    logger.info(os.path.join(settings.SITE_ROOT, share_user_album.link))
                    logger.info(os.path.join(settings.SITE_ROOT, share_user_link))
                    file_path = os.path.join(settings.UPLOAD_FILES_PATH, self.current_user.cid, category_dir)
                    if not os.path.exists(file_path):
                        os.makedirs(file_path)
                    shutil.copyfile(os.path.join(settings.SITE_ROOT, share_user_album.link), os.path.join(settings.SITE_ROOT, share_user_link))
                    album = PhotoAlbum(app_user_cid=self.current_user.cid, name=share_user_album.name, album_type=share_user_album.album_type,
                                       attribute=STATUS_ALBUM_TYPE_SHARE, pir_key=share_user_album.pir_key, status=share_user_album.status,
                                       link=share_user_link,share_list=[share_user_album.cid])
                    await album.save()
                    share_user_album.share_list.append(album.cid)
                    await share_user_album.save()
                    r_dict['link'] = album.link
                    r_dict['code'] = 1000
                else:
                    r_dict = {'code': 1004}
            else:
                r_dict = {'code': 1006}
        except Exception:
            logger.error(traceback.format_exc())

        return r_dict



class AlbumEditHandler(WechatAppletHandler):
    '''
    修改相册名称         error
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        修改相册名称接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            name = self.get_i_argument('name')
            album_cid = self.get_i_argument('album_cid')
            album = await PhotoAlbum.find_one(dict(cid=album_cid))
            if not album:
                r_dict = {'code': 1002}  # 相册编号为空或者无效
                return r_dict
            if not name:
                r_dict = {'code': 1003}  # 相册名称为空
                return r_dict
            album_data = await PhotoAlbum.find_one(
                dict(name=name, app_user_cid=self.current_user.cid, album_type=album.album_type))
            if album_data and album_data.cid != album_cid:
                r_dict = {'code': 1004}  # 相册名称不能重复
                return r_dict
            if len(name) >= 25:
                r_dict = {'code': 1005}  # 相册名称规则不匹配
                return r_dict
            if album.name == 'default':
                return r_dict
            album.name = name
            await album.save()
            r_dict = {'code': 1000}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class AlbumDeleteHandler(WechatAppletHandler):
    '''
    删除相册
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        删除相册接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            album_name = self.get_i_argument('name')
            category = self.get_i_argument('category')
            type = self.get_i_argument('type')
            album = await PhotoAlbum.find_one(dict(name=album_name,app_user_cid=self.current_user.cid))
            if not album:
                r_dict = {'code': 1005}  # 相册名称为空或者无效
                return r_dict
            if not type:
                r_dict = {'code': 1001}  # 类型为空
            if int(type) != STATUS_ALBUM_TYPE_PIC:
                r_dict = {'code': 1003}  # 类型不满足要求
            if not category:
                r_dict = {'code': 1002}  # 类别为空
                return r_dict

            if int(category) != STATUS_ALBUM_ATTR_SELF:
                r_dict = {'code': 1004}  # 类别不满足要求 不是自建相册
                return r_dict
            album.status = 0
            album.updated_dt = datetime.datetime.now()
            await album.save()
            share_users_list = album.share_list
            for i in share_users_list:
                album_share_cid = await PhotoAlbum.find_one(dict(cid=i))
                album_share_cid.status = 0
                album_share_cid.updated_dt = datetime.datetime.now()
                await album_share_cid.save()

            r_dict = {'code': 1000}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class FileDeleteHandler(WechatAppletHandler):
    '''
    图片/视频删除，进入回收站，支持多选
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        删除进回收站，支持多选
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            album_cid = self.get_i_argument('album_cid')
            file_cid_list = self.get_i_argument('file_cid_list')
            album = await PhotoAlbum.count(dict(cid=album_cid))
            if not album:
                r_dict = {'code': 1002}  # 相册编号为空或者无效
                return r_dict
            if not file_cid_list:
                return r_dict  # 未有选中的照片
            update_requests = []
            for i in file_cid_list:
                update_requests.append(UpdateOne({'cid': i},
                                                 {'$set': {'status': STATUS_FILE_INVALID,
                                                           'updated_dt': datetime.datetime.now(),
                                                           'updated_id': self.current_user.oid}}))
            if update_requests:
                modified_count = await File.update_many(update_requests)
                r_dict['code'] = 1000
                r_dict['modified_count'] = modified_count
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class AlbumRealDeleteHandler(WechatAppletHandler):
    '''
    图片/视频删除，进入回收站，支持多选
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        删除进回收站，支持多选
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            type = self.get_i_argument('type')
            category = self.get_i_argument('category')
            name = self.get_i_argument('name')
            album = await PhotoAlbum.find_one(dict(name=name,app_user_cid=self.current_user.cid))
            if not album:
                r_dict = {'code': 1005}  # 相册名称有误或相册不存在
                return r_dict
            if not type:
                r_dict = {'code': 1001}  # 类型为空
                return r_dict
            if int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1003}  # 类型不匹配
                return r_dict
            if not category:
                r_dict = {'code': 1002}  # 类别为空
                return r_dict
            if int(category) not in STATUS_ALBUM_ATTR_LIST:
                r_dict = {'code': 1004}  # 类别不匹配
                return r_dict
            if album.attribute == STATUS_ALBUM_ATTR_SELF and album.status != STATUS_ALBUM_INVALID:
                return r_dict   # 此时不满足删除要求
            if album.attribute == STATUS_ALBUM_TYPE_SHARE:
                deleted_count = await PhotoAlbum.delete_many(dict(cid=album.cid))
                super_album = await PhotoAlbum.find_one(dict(cid=album.share_list[0]))
                super_album.share_list.remove(album.cid)
                super_album.updated_dt = datetime.datetime.now()
                await super_album.save()   # 同时更新分享人列表中的数据
                r_dict['deleted_count'] = deleted_count
                r_dict['code'] = 1000
            if album.attribute == STATUS_ALBUM_ATTR_SELF and album.status == STATUS_ALBUM_INVALID:
                album.share_list.append(album.cid)
                deleted_count = 0
                for i in album.share_list:
                    await PhotoAlbum.delete_many(dict(cid=i))
                    deleted_count +=1
                r_dict['deleted_count'] = deleted_count
                r_dict['code'] = 1000
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class AlbumEditNameHandler(WechatAppletHandler):
    '''
    修改相册名称
    '''

    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        修改相册名称接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            album_name = self.get_i_argument('name')
            category = self.get_i_argument('category')
            type = self.get_i_argument('type')
            rename = self.get_i_argument('rename')
            album = await PhotoAlbum.find_one(dict(name=album_name, app_user_cid=self.current_user.cid))
            if not album:
                r_dict = {'code': 1005}  # 相册名称为空或者无效
                return r_dict
            if not type:
                r_dict = {'code': 1001}  # 类型为空
            if int(type) != STATUS_ALBUM_TYPE_PIC:
                r_dict = {'code': 1003}  # 类型不满足要求
            if not category:
                r_dict = {'code': 1002}  # 类别为空
                return r_dict
            if not rename or len(rename) >= 25:
                r_dict = {'code': 1006}  # 相册名称规则不匹配
                return r_dict
            if int(category) != STATUS_ALBUM_ATTR_SELF:
                r_dict = {'code': 1004}  # 类别不满足要求 不是自建相册
                return r_dict
            album_count = await PhotoAlbum.count(dict(app_user_cid=self.current_user.cid,name=rename))
            if album.name != rename:
                if album_count != 0:
                    r_dict = {'code': 1006}  # 相册名称规则不匹配
                    return r_dict
            album.name = rename
            # raw_link = settings.SITE_ROOT + '\\'+ album.link
            raw_link = r'{}/{}'.format(settings.SITE_ROOT,album.link)
            # link = 'static\\files\\'+self.current_user.cid+ '\picture\\'+rename+'.txt'
            link = r'static/files/{}/picture/{}.txt'.format(self.current_user.cid,rename)
            album.link=link
            album.updated_dt = datetime.datetime.now()
            share_users_list = album.share_list
            new_link = r'{}/{}'.format(settings.SITE_ROOT,link)
            for i in share_users_list:
                album_share_cid = await PhotoAlbum.find_one(dict(cid=i))
                album_share_cid.name = rename
                album_share_cid.link = link
                album_share_cid.updated_dt = datetime.datetime.now()
                await album_share_cid.save()
            await album.save()
            os.rename(raw_link,new_link)
            r_dict = {'code': 1000}
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


class ImportAlbumHandler(WechatAppletHandler):
    '''
        图片相册文件导入
        '''
    @decorators.render_json
    @decorators.app_authenticated
    async def post(self, *args, **kwargs):
        '''
        上传相册对象、视频接口
        :param args:
        :param kwargs:
        :return:
        '''
        r_dict = {'code': 0}
        try:
            public_key = self.get_i_argument('public_key')
            if not public_key:
                r_dict = {'code': 1001}  # 公钥为空
                return r_dict
            type = self.get_i_argument('type')
            if int(type) not in STATUS_ALBUM_TYPE_LIST:
                r_dict = {'code': 1002}  # 类型为空或不在类型中
                return r_dict
            msg = await PhotoAlbum.find_one(
                dict(app_user_cid=self.current_user.cid, album_type=int(type), pir_key=public_key))
            if not msg:
                r_dict = {'code': 1003}  # 该相册不存在
                return r_dict
            r_dict['link'] = "/" + msg.link
            r_dict['code'] = 1000
        except Exception:
            logger.error(traceback.format_exc())
        return r_dict


URL_MAPPING_LIST = [
    url(r'/api/album/list/', AlbumListHandler, name='api_album_list'),
    url(r'/api/album/create/', AlbumCreateHandler, name='api_album_create'),
    url(r'/api/album/upload/', AlbumUplodeHandler, name='api_album_uplode'),
    url(r'/api/album/import_share/', AlbumImportHandler, name='api_album_import'),
    url(r'/api/album/edit/', AlbumEditHandler, name='api_album_edit'),
    url(r'/api/album/delete/', AlbumDeleteHandler, name='api_album_delete'),
    url(r'/api/file/delete/', FileDeleteHandler, name='api_file_delete'),
    url(r'/api/album/real_delete/', AlbumRealDeleteHandler, name='api_file_real_delete'),
    url(r'/api/album/edit/name/', AlbumEditNameHandler, name='api_album_edit_name'),
    url(r'/api/album/import/', ImportAlbumHandler, name='api_album_import')

]
