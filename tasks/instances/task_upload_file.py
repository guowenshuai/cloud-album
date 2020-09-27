# !/usr/bin/python
# -*- coding:utf-8 -*-
from logger import log_utils
from services import file_service
from tasks import app

logger = log_utils.get_logging('tasks_upload_file', 'tasks_upload_file.log')


@app.task(bind=True, queue='upload_file')
def upload_file(self, album_cid, app_user_cid, file, task_cid, category):
    file_service.upload_file(album_cid=album_cid, app_user_cid=app_user_cid,
                             file=file, task_cid=task_cid, category=category)
