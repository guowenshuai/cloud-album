# !/usr/bin/python
# -*- coding:utf-8 -*-
from logger import log_utils
from tasks.instances.task_upload_file import upload_file

logger = log_utils.get_logging()


def upload_file_to_ipfs(album_cid, app_user_cid, file, task_cid,category):
    """
    异步上传文件到ipfs
    """
    upload_file.delay(album_cid=album_cid, app_user_cid=app_user_cid, file=file, task_cid=task_cid,category=category)
