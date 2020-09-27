# !/usr/bin/python
# -*- coding:utf-8 -*-
from datetime import datetime
from tornado.web import url
from db.models import AppVersion
from web import BaseHandler, decorators


class VersionHandler(BaseHandler):
    pass