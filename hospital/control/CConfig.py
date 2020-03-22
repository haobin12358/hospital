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
from hospital.models.config import Banner, Setting, Characteristicteam, Honour

class CConfig:

    @admin_required
    def set_banner(self):
        """banner创建/编辑/删除"""
        print(request.data)
        data = parameter_required(('bnpicture', "bnsort",))
        bnid = data.get('bnid')
        bn_dict = {'BNpicture': data.get('bnpicture'),
                    'BNsort': data.get('bnsort'),
                    'contentlink': data.get('contentlink')}
        with db.auto_commit():
            if not bnid:
                """新增"""
                bn_dict['BNid'] = str(uuid.uuid1())
                bn_dict['ADid'] = getattr(request, 'user').id
                bn_instance = Banner.create(bn_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                bn_instance = Banner.query.filter_by_(BNid=bnid).first_('未找到该轮播图信息')
                if data.get('delete'):
                    bn_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    bn_instance.update(bn_dict, null='not')
                    msg = '编辑成功'
            db.session.add(bn_instance)
        return Success(message=msg, data={'bnid': bn_instance.BNid})

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
            "STvalue": data.get("stvalue"),
            "STtype": 1
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

    def get_about_us(self):
        """关于我们"""
        about_us = Setting.query.filter(Setting.isdelete == 0, Setting.STtype == 2).all()
        about_us_dict = {}
        for row in about_us:
            about_us_dict[row["STname"]] = row["STvalue"]
        # 主图
        if "min_pic" not in about_us_dict:
            about_us_dict["min_pic"] = ""
        # 医院名称
        if "name" not in about_us_dict:
            about_us_dict["name"] = ""
        # 地址
        if "address" not in about_us_dict:
            about_us_dict["address"] = ""
        # 路线
        if "route" not in about_us_dict:
            about_us_dict["route"] = ""
        # 联系电话
        if "telphone" not in about_us_dict:
            about_us_dict["telphone"] = ""
        # 简介
        if "synopsls" not in about_us_dict:
            about_us_dict["synopsls"] = ""
        # 环境
        if "environment" not in about_us_dict:
            about_us_dict["environment"] = ""
        # 官网
        if "official_website" not in about_us_dict:
            about_us_dict["official_website"] = ""

        team = Characteristicteam.query.filter(Characteristicteam.isdelete == 0).all() # 特色科室/专家团队
        print(team)
        print(about_us_dict)
        honour = Honour.query.filter(Honour.isdelete == 0).all() # 医院荣誉
        about_us_dict["characteristicteam"] = team
        if not team:
            about_us_dict["characteristicteam"] = {}
        about_us_dict["honour"] = honour
        if not honour:
            about_us_dict["honour"] = {}
        return Success(data=about_us_dict)

    @admin_required
    def set_about_us(self):
        """更新除了团队荣誉和特色科室以外个人中心部分"""
        data = parameter_required(('min_pic', "name", "address", "route", "telphone", "synopsls", "environment", "official_website",))
        setting_dict = {
            "min_pic": data.get("min_pic"),
            "name": data.get("name"),
            "address": data.get("address"),
            "route": data.get("route"),
            "telphone": data.get("telphone"),
            "synopsls": data.get("synopsls"),
            "environment": data.get("environment"),
            "official_website": data.get("official_website"),
        }

        for row in setting_dict.keys():
            with db.auto_commit():
                setting_id = Setting.query.filter(Setting.isdelete == 0, Setting.STname == row).first()
                setting_dict = {
                    "STname": row,
                    "STvalue": data[row],
                    "STtype": 2
                }
                if not setting_id:
                    setting_dict["STid"] = str(uuid.uuid1())
                    setting_instance = Setting.create(setting_dict)
                    msg = "成功创建"
                else:
                    setting_instance = Setting.query.filter_by_(STid=setting_id.STid).first_('未找到该变量')
                    setting_instance.update(setting_dict, null='not')
                    msg = "成功更新"
                db.session.add(setting_instance)
        return Success(message=msg)

    @admin_required
    def set_characteristic_team(self):
        """创建/更新/删除特色科室"""
        data = parameter_required(('ctpicture', 'ctname', 'ctposition', 'ctoffice'))
        ctid = data.get('ctid')
        ct_dict = {
            'CTpicture': data.get('ctpicture'),
            'CTname': data.get('ctname'),
            'CTposition': data.get('ctposition'),
            'CToffice': data.get('ctoffice')
        }
        with db.auto_commit():
            if not ctid:
                """新增"""
                ct_dict['CTid'] = str(uuid.uuid1())
                ct_instance = Characteristicteam.create(ct_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                ct_instance = Characteristicteam.query.filter_by_(CTid=ctid).first_('未找到该特色科室信息')
                if data.get('delete'):
                    ct_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    ct_instance.update(ct_dict, null='not')
                    msg = '编辑成功'
            db.session.add(ct_instance)

        return Success(message=msg, data={'ctid': ct_instance.CTid})

    @admin_required
    def set_honour(self):
        """创建/更新/删除团队荣誉"""
        data = parameter_required(('hopicture', 'hotext'))
        hoid = data.get('hoid')
        ho_dict = {
            'HOpicture': data.get('hopicture'),
            'HOtext': data.get('hotext')
        }
        with db.auto_commit():
            if not hoid:
                """新增"""
                ho_dict['HOid'] = str(uuid.uuid1())
                ho_instance = Honour.create(ho_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                ho_instance = Honour.query.filter_by_(HOid=hoid).first_('未找到该特色科室信息')
                if data.get('delete'):
                    ho_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    ho_instance.update(ho_dict, null='not')
                    msg = '编辑成功'
            db.session.add(ho_instance)
        return Success(message=msg, data={'hoid': ho_instance.HOid})

