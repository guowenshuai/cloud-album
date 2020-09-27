from db import STATUS_TASK_TRANSFER_DONE, STATUS_FILE_INVALID, STATUS_FILE_EFFECFIVE, STATUS_FILE_UPLOAD_TYPE_PIC
from db.models import File, Task
from ipfs.ipfs_utils import ipfs
from datetime import datetime
from PIL import Image
from io import BytesIO
import os
import settings


def upload_file(album_cid, app_user_cid, file, task_cid, category):
    api = ipfs.client
    file_hash = api.add_bytes(file.body)
    new_file = File.sync_find_one(dict(photo_album_cid=album_cid, app_user_cid=app_user_cid,
                                       hash=file_hash, category=category))
    if new_file:
        # 如果相同hash，相同用户，相同相册对应文件 回收站中有 再次上传 会更新状态与名称
        if new_file.status == STATUS_FILE_INVALID:
            new_file.status = STATUS_FILE_EFFECFIVE
            new_file.name = file.filename
            new_file.sync_save()
        else:
            task = Task.sync_find_one(dict(cid=task_cid))
            task.sync_delete()
    else:

        new_file = File(photo_album_cid=album_cid, app_user_cid=app_user_cid,
                        hash=file_hash, category=category)
        new_file.name = file.filename
        if category == STATUS_FILE_UPLOAD_TYPE_PIC:
            # 服务端生成缩略图
            # 初始化附件目录
            file_name = file_hash + '.png'
            file_dir = os.path.join(settings.UPLOAD_FILES_PATH, app_user_cid, album_cid)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            final_name = os.path.join(file_dir, file_name)
            image = Image.open(BytesIO(file.body))
            # image.thumbnail((128, 128), Image.ANTIALIAS)
            image = image.resize((128, 128), Image.ANTIALIAS)
            quality_val = 90
            image.save(final_name, 'png', quality=quality_val)
            new_file.thumbnail = '/static'+final_name.split('static')[-1]
        new_file.sync_save()
        task = Task.sync_find_one(dict(cid=task_cid))
        task.end_time = datetime.now()
        task.status = STATUS_TASK_TRANSFER_DONE
        task.sync_save()

