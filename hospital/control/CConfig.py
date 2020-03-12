"""
本文件用于处理后台管理员及管理员操作行为
create user: haobin12358
last update time:2020/3/13 03:53
"""
import uuid
from flask import request, current_app
from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.register_ext import db
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.models.config import Banner, Setting

class CConfig:

    @admin_required
    def set_banner(self):
        """banner创建/编辑/删除"""
        print(request.data)
        data = parameter_required(('bnpicture', "bnsort",))
        mpbid = data.get('mpbid')
        bn_dict = {'BNpicture': data.get('bnpicture'),
                    'BNsort': data.get('bnsort'),
                    'contentlink': data.get('contentlink')}
        with db.auto_commit():
            if not mpbid:
                """新增"""
                bn_dict['BNid'] = str(uuid.uuid1())
                bn_dict['ADid'] = getattr(request, 'user').id
                bn_instance = Banner.create(bn_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                bn_instance = Banner.query.filter_by_(MPBid=mpbid).first_('未找到该轮播图信息')
                if data.get('delete'):
                    bn_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    bn_instance.update(bn_dict, null='not')
                    msg = '编辑成功'
            db.session.add(bn_instance)
        return Success(message=msg, data={'mpbid': bn_instance.BNid})

    def list_banner(self):
        """小程序轮播图获取"""
        bn = Banner.query.filter(Banner.isdelete == 0).order_by(Banner.BNsort.asc(),
                                                         Banner.createtime.desc()).all()
        [x.hide('ADid') for x in bn]
        return Success(data=bn)

    def get_csd(self):
        "获取客服customer service department二维码"
        csd = Setting.query.filter(Setting.isdelete == 0, Setting.STname == "CSD").first()
        return Success(data=csd)

    @admin_required
    def set_csd(self):
        "设置or更新客服customer service department二维码"
        data = parameter_required(('stvalue',))
        csd = Setting.query.filter(Setting.isdelete == 0, Setting.STname == "CSD").first()
        csd_dict = {
            "STname": "CSD",
            "STvalue": data.get("stvalue")
        }
        with db.auto_commit():
            if not csd:
                csd_dict["STid"] = str(uuid.uuid1())
                csd_instance = Setting.create(csd_dict)
                msg = "创建客服二维码成功"
            else:
                csd_instance = Setting.query.filter_by_(STid=csd.STid).first_('未找到该客服二维码')
                csd_instance.update(csd_dict, null='not')
                msg = "更新客服二维码成功"
            db.session.add(csd_instance)
        return Success(message=msg)