# !/usr/bin/python
# -*- coding:utf-8 -*-

import msgpack
from caches.redis_utils import RedisCache
from db.models import  AdministrativeDivision
from enums import  KEY_ADMINISTRATIVE_DIVISION
from motorengine import ASC, FacadeO
from motorengine.stages import MatchStage, LookupStage, SortStage


def get_document_needless(document):
    if document and isinstance(document, dict):
        needless = document.get('needless')
        if isinstance(needless, dict):
            return needless
    return {}


async def get_administrative_division():
    ad_data = RedisCache.get(KEY_ADMINISTRATIVE_DIVISION)
    if ad_data:
        return msgpack.unpackb(ad_data, raw=False)

    def ad_2_dict(ad):
        result = {}
        if ad:
            if isinstance(ad, (FacadeO, AdministrativeDivision)):
                try:
                    result['code'] = ad.code
                except Exception:
                    result['code'] = ad.post_code
                if not ad.parent_code:
                    result['name'] = ad.title.replace('省', '').replace('市', '').replace('自治区', ''). \
                        replace('壮族', '').replace('回族', '').replace('维吾尔', '')
                else:
                    result['name'] = ad.title
                if ad.parent_code:
                    result['parent_code'] = ad.parent_code
                result['sub'] = []
                if ad.sub_list:
                    for su_ad in ad.sub_list:
                        if su_ad:
                            result['sub'].append(ad_2_dict(su_ad))
            else:
                result['code'] = ad.get('post_code')
                parent_code = ad.get('parent_code')

                if not parent_code:
                    result['name'] = ad.get('title').replace('省', '').replace('市', '').replace('自治区', ''). \
                        replace('壮族', '').replace('回族', '').replace('维吾尔', '')
                else:
                    result['name'] = ad.get('title')

                if parent_code:
                    result['parent_code'] = parent_code
                result['sub'] = []
                sub_list = ad.get('sub_list')
                if sub_list:
                    for su_ad in sub_list:
                        if su_ad:
                            result['sub'].append(ad_2_dict(su_ad))

        return result

    ad_cursor = AdministrativeDivision.aggregate([
        MatchStage(dict(parent_code=None)),
        LookupStage(AdministrativeDivision, as_list_name='sub_list', let=dict(city_parent_code='$post_code'),
                    pipeline=[
                        MatchStage({
                            '$expr': {
                                '$and': [{'$eq': ['$parent_code', '$$city_parent_code']}]
                            }
                        }),
                        SortStage([('post_code', ASC)]),
                        LookupStage(AdministrativeDivision, as_list_name='sub_list',
                                    let=dict(area_parent_code='$post_code'),
                                    pipeline=[
                                        MatchStage({
                                            '$expr': {
                                                '$and': [{'$eq': ["$parent_code", "$$area_parent_code"]}]
                                            }
                                        }),
                                        SortStage([('post_code', ASC)])
                                    ])
                    ]),
        SortStage([('post_code', ASC)])
    ])
    ad_list = []
    while await ad_cursor.fetch_next:
        ad_dict = ad_2_dict(ad_cursor.next_object())
        if ad_dict:
            ad_list.append(ad_dict)
    if ad_list:
        RedisCache.set(KEY_ADMINISTRATIVE_DIVISION, msgpack.packb(ad_list))
    return ad_list


async def do_different_administrative_division(ad_code_list: list):
    """
    区分行政区划等级
    :param ad_code_list: 行政区划编码列表
    :return: (省份, 城市, 区/县)
    """
    province_code_list, city_code_list, district_code_list = [], [], []
    if ad_code_list:
        ad_cursor = AdministrativeDivision.find({'code': {'$in': ad_code_list}})
        while await ad_cursor.fetch_next:
            ad: AdministrativeDivision = ad_cursor.next_object()
            if ad:
                if ad.level == 'P':
                    province_code_list.append(ad.code)
                elif ad.level == 'C':
                    city_code_list.append(ad.code)
                elif ad.level == 'D':
                    district_code_list.append(ad.code)
    return province_code_list, city_code_list, district_code_list


async def do_different_administrative_division2(ad_code_list: list):
    """
    区分行政区划等级
    :param ad_code_list: 行政区划编码列表
    :return: (省份, 城市, 区/县)
    """
    province_code_list, city_code_list, district_code_list = [], [], []

    if not ad_code_list:
        raise ValueError('There are no manageable areas for this account.')

    ad_cursor = AdministrativeDivision.find({'code': {'$in': ad_code_list}})
    while await ad_cursor.fetch_next:
        ad: AdministrativeDivision = ad_cursor.next_object()
        if ad:
            if ad.level == 'P':
                province_code_list.append(ad.code)
                city_code_list += await AdministrativeDivision.distinct('code', {'parent_code': ad.code})
            elif ad.level == 'C':
                city_code_list.append(ad.code)
                province_code_list.append(ad.parent_code)
            elif ad.level == 'D':
                district_code_list.append(ad.code)
    province_code_list.sort()
    city_code_list.sort()
    district_code_list.sort()
    return list(set(province_code_list)), list(set(city_code_list)), list(set(district_code_list))
