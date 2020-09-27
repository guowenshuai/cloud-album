# !/usr/bin/python
# -*- coding:utf-8 -*-
from tornado.web import url
from web import BaseHandler


class IndexHandler(BaseHandler):

    def get(self):
        self.redirect(self.reverse_url('backoffice_index'))
        return


URL_MAPPING_LIST = [
    url(r'/', IndexHandler, name='index'),
]
