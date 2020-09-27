# !/usr/bin/python
# -*- coding:utf-8 -*-


import datetime

from celery import Celery
from kombu import Queue, Exchange

import settings
from db.models import AdministrativeDivision


class TaskCelery(Celery):
    def __init__(self, main=None, loader=None, backend=None, amqp=None, events=None, log=None, control=None,
                 set_as_current=True, tasks=None, broker=None, include=None, changes=None, config_source=None,
                 fixups=None, task_cls=None, autofinalize=True, namespace=None, strict_typing=True, **kwargs):
        super(TaskCelery, self).__init__(
            main=main, loader=loader, backend=backend, amqp=amqp, events=events, log=log, control=control,
            set_as_current=set_as_current, tasks=tasks, broker=broker, include=include, changes=changes,
            config_source=config_source, fixups=fixups, task_cls=task_cls, autofinalize=autofinalize,
            namespace=namespace, strict_typing=strict_typing, **kwargs)

    def task(self, *args, **opts):
        if not opts.get('queue'):
            opts['queue'] = 'default'
        return super(TaskCelery, self).task(*args, **opts)

    def update_config(self, *args, **kwargs):
        """
        更新配置
        :param args:
        :param kwargs:
        :return:
        """
        super(TaskCelery, self).conf.update(*args, **kwargs)

    def get_config(self, name):
        """
        获取配置
        :param name: 配置名
        :return:
        """
        return self.conf.find_value_for_key(name)

    def register_schedule(self, schedule_name: str, func, periodic, *args):
        """
        注册时间循环排班任务
        :return:
        """
        schedule = {
            'task': func,
            'schedule': periodic,
            'args': args
        }
        self.__register_beat_schedule(schedule_name, schedule)

    def __register_beat_schedule(self, schedule_name, schedule: dict):
        if schedule_name and schedule:
            # 所有已注册排版任务
            beat_schedule = self.get_config('beat_schedule')
            if beat_schedule is None:
                beat_schedule = {}

            beat_schedule[schedule_name] = schedule

            self.update_config(beat_schedule=beat_schedule)


def get_task_celery_instance(instance_name, config_module) -> TaskCelery:
    """
    获取一个新的Celery任务实例
    :param instance_name: 实例名称
    :param config_module: 配置对象
    :param use_db: 是否使用DB
    :return:
    """
    if not instance_name:
        raise ValueError('"instance_name" is required.')
    if not isinstance(instance_name, str):
        raise TypeError('"instance_name" only a str.')

    c_instance = TaskCelery(main=instance_name)
    c_instance.config_from_object(config_module)

    return c_instance


DEFAULT_QUEUE = Queue(name='default', exchange=Exchange('celery'), routing_key='celery')


def get_tasks_imports_and_queues():
    """
    获取任务模块&队列
    :return:
    """
    imports, queues = [], [DEFAULT_QUEUE]
    for task_func, queue_name in settings.TASKS_FUNC_MODULE_CFG_LIST:
        if task_func:
            imports.append(task_func)
            if queue_name and not queue_name == 'default':
                queue = Queue(name=queue_name, exchange=Exchange(queue_name), routing_key=queue_name)
                queues.append(queue)
    return imports, queues





def get_yesterday():
    """
    得到前一天凌晨12点之前的时间
    :return:
    """
    time_match = (datetime.datetime.now() + datetime.timedelta(days=-1)).replace(hour=23, minute=59, second=59,
                                                                                 microsecond=999)
    return time_match





def get_region_match(race):
    city_list = AdministrativeDivision.sync_distinct('code', {'parent_code': race.province_code})
    city_name_list = AdministrativeDivision.sync_distinct('title', {'parent_code': race.province_code})
    dist_list = []
    for city in city_list:
        dist_list += AdministrativeDivision.sync_distinct('title', {'parent_code': city})

    return {'city': {'$in': city_name_list}, 'district': {'$in': dist_list}}
