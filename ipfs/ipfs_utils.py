# !/usr/bin/python
# -*- coding:utf-8 -*-


import ipfsapi


class Ipfs(object):
    __client = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Ipfs, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @property
    def __api(self):
        if not self.__client:
            self.__client = ipfsapi.connect('39.101.196.152', 8888, chunk_size=1024 * 1024 * 100)

        return self.__client

    @property
    def client(self):
        return self.__api


ipfs = Ipfs()
