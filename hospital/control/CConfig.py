"""
本文件用于处理后台管理员及管理员操作行为
create user: haobin12358
last update time:2020/3/13 03:53
"""
import uuid, datetime
from flask import request, current_app
from hospital.extensions.interface.user_interface import admin_required, is_admin, is_hign_level_admin, token_required, \
    is_doctor, is_user
from hospital.extensions.register_ext import db
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import AuthorityError, SystemError
from hospital.extensions.request_handler import token_to_user_
from hospital.models.config import Banner, Setting, Characteristicteam, Honour, PointTask
from hospital.models.user import UserIntegral, User
from hospital.config.enums import PointTaskType

class CConfig:

    @admin_required
    def set_banner(self):
        """banner创建/编辑/删除"""
        data = parameter_required(('bnpicture', "bnsort",) if not request.json.get('delete') else('bnid', ))
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
        data = parameter_required(('ctpicture', 'ctname', 'ctposition', 'ctoffice')
                                  if not request.json.get('delete') else('ctid', ))
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
        data = parameter_required(('hopicture', 'hotext') if not request.json.get('delete') else('hoid',))
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

    def set_vip_price(self):
        """设置会员价格"""
        data = parameter_required(('VIP',))
        csd = Setting.query.filter(Setting.isdelete == 0, Setting.STname == "VIP").first()
        csd_dict = {
            "STname": "VIP",
            "STvalue": data.get("VIP"),
            "STtype": 5
        }
        with db.auto_commit():
            if not csd:
                csd_dict["STid"] = str(uuid.uuid1())
                csd_instance = Setting.create(csd_dict)
                msg = "创建会员价格成功"
            else:
                csd_instance = Setting.query.filter_by_(STid=csd.STid).first_('未找到会员价格')
                csd_instance.update(csd_dict, null='not')
                msg = "更新会员价格成功"
            db.session.add(csd_instance)
        return Success(message=msg)

    def get_vip_price(self):
        """获取会员价格"""
        csd = Setting.query.filter(Setting.isdelete == 0, Setting.STname == "VIP").first()
        return Success(data=csd)

    @token_required
    def get_pointtask(self):
        """获取任务列表"""
        args = parameter_required(('token', ))
        # user = token_to_user_(args.get('token'))
        # user = getattr(request, 'user')
        if is_doctor():
            return AuthorityError()
        else:
            pointtask_list = PointTask.query.filter(PointTask.isdelete == 0).order_by(PointTask.PTid.asc()).all()
            if is_user():
                # 前台需要增加是否可完成的状态
                for pointtask in pointtask_list:
                    userintegral = UserIntegral.query.filter(UserIntegral.isdelete == 0, UserIntegral.UItrue == 0,
                                                             UserIntegral.UItype == 1,
                                                             UserIntegral.UIaction == pointtask.PTtype).all()
                    if userintegral:
                        pointtask.fill("is_get", 1)
                    else:
                        pointtask.fill("is_get", 0)
                    time_now = datetime.datetime.now()
                    pttime = pointtask.PTtime or 0
                    if pttime > 0:
                        userintegral_end = UserIntegral.query.filter(UserIntegral.isdelete == 0,
                                                                     UserIntegral.UItrue == 1,
                                                                     UserIntegral.UItype == 1,
                                                                     UserIntegral.UIaction == pointtask.PTtype,
                                                                     UserIntegral.createtime >
                                                                     datetime.datetime(time_now.year,
                                                                                       time_now.month,
                                                                                       time_now.day, 0, 0, 0),
                                                                     UserIntegral.createtime <
                                                                     datetime.datetime(time_now.year,
                                                                                       time_now.month,
                                                                                       time_now.day, 23, 59, 59)
                                                                     ).all()
                        if pttime <= len(userintegral_end):
                            pointtask["is_get"] = 2
                    elif pttime < 0:
                        pttime = abs(pttime)
                        userintegral_end = UserIntegral.query.filter(UserIntegral.isdelete == 0,
                                                                     UserIntegral.UItrue == 1,
                                                                     UserIntegral.UItype == 1,
                                                                     UserIntegral.UIaction == pointtask.PTtype
                                                                     ).all()
                        if pttime <= len(userintegral_end):
                            pointtask["is_get"] = 2
                    else:
                        pass

        return Success(message="获取任务列表成功", data=pointtask_list)

    def update_pointtask(self):
        """更新任务积分以及次数"""
        # 后台更新次数以及积分数，负表示仅限次数，0表示无限次，正表示每日可完成次数
        if not (is_admin() or is_hign_level_admin()):
            return AuthorityError()
        data = parameter_required('ptid', 'ptnumber', 'pttime', 'pticon')
        pt_dict = {
            "PTnumber": data.get('ptnumber'),
            "PTtime": data.get('pttime'),
            "PTicon": data.get('pticon')
        }
        pt_instance = PointTask.query.filter(PointTask.PTid == data.get('ptid')).first_("未找到该任务")
        with db.auto_commit():
            pt_instance.update(pt_dict, null='not')
            db.session.add(pt_instance)
        return Success(message="更新任务成功")

    def get_integral(self):
        """获取个人积分变动情况"""
        # 后台可筛选，前台默认用户token
        args = parameter_required(('token', ))
        filter_args = [UserIntegral.isdelete == 0]
        user = token_to_user_(args.get('token'))
        if user.model == "User":
            filter_args.append(UserIntegral.USid == user.id)
            filter_args.append(UserIntegral.UItrue == 1)
        else:
            if not (is_admin() or is_hign_level_admin()):
                return AuthorityError()
            if args.get('usid'):
                filter_args.append(UserIntegral.USid == args.get('usid'))
        userIntegral = UserIntegral.query.filter(*filter_args).order_by(UserIntegral.createtime.desc()).all_with_page()
        for user_item in userIntegral:
            user = User.query.filter(User.USid == user_item.USid).first()
            user_item.fill('usname', user.USname)
            user_item.fill('utname', PointTaskType(user_item.UIaction).zh_value)
            user_item.fill('createtime', user.createtime)
        return Success(message="获取积分变动成功", data=userIntegral)

    def _judge_point(self, pttype, uitype, usid, uiintegral=None):
        """判断积分是否可以写入, 如果可以，则写入，如果不可以，则pass"""
        # 前台多api调用，传入type，基于pttime和len(userintegral)判断是否写入
        with db.auto_commit():
            if uitype == 1:
                """收入"""
                pointtask = PointTask.query.filter(PointTask.PTtype == pttype).first_("该类型错误")
                pttime = int(pointtask.PTtime or 0)
                ui_dict = {
                    "UIid": str(uuid.uuid1()),
                    "USid": usid,
                    "UIintegral": pointtask.PTnumber,
                    "UIaction": pttype,
                    "UItype": uitype,
                    "UItrue": 0
                }
                if pttime > 0:
                    # 每日限制次数
                    time_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                                   datetime.datetime.now().day, 0, 0, 0)
                    time_end = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                                   datetime.datetime.now().day, 23, 59, 59)
                    # 当日已完成次数
                    userintegral = UserIntegral.query.filter(UserIntegral.createtime > time_start,
                                                             UserIntegral.createtime < time_end,
                                                             UserIntegral.isdelete == 0,
                                                             UserIntegral.UIaction == pttype).all()
                    if len(userintegral) >= pttime:
                        return 0
                    else:
                        ui_instance = UserIntegral.create(ui_dict)
                elif pttime < 0:
                    # 一次性
                    userintegral = UserIntegral.query.filter(UserIntegral.isdelete == 0,
                                                             UserIntegral.UIaction == pttype).all()
                    if userintegral:
                        return 0
                    else:
                        ui_instance = UserIntegral.create(ui_dict)
                else:
                    # 不限次
                    ui_instance = UserIntegral.create(ui_dict)
            elif uitype == 2:
                """支出"""
                ui_dict = {
                    "UIid": str(uuid.uuid1()),
                    "USid": usid,
                    "UIintegral": uiintegral,
                    "UIaction": pttype,
                    "UItype": uitype,
                    "UItrue": 0
                }
                ui_instance = UserIntegral.create(ui_dict)
            else:
                return SystemError("服务端异常")
            db.session.add(ui_instance)
            return 1

    def get_point(self):
        """领取积分"""
        # 前台领取积分，基于ptid查找uitrue=0且uiaction=pttype的第一条数据，更新uitrue字段
        data = parameter_required(('ptid', ))
        args = request.args.to_dict()
        user = token_to_user_(args['token'])
        pointtask = PointTask.query.filter(PointTask.isdelete == 0,
                                           PointTask.PTid == data.get('ptid')).first_("未找到该任务")
        pttype = pointtask.PTtype
        userintegral = UserIntegral.query.filter(UserIntegral.isdelete == 0, UserIntegral.USid == user.id,
                                                 UserIntegral.UItype == 1, UserIntegral.UItrue == 0,
                                                 UserIntegral.UIaction == pttype)\
            .first_("无可领取积分")
        with db.auto_commit():
            ui_instance = UserIntegral.query.filter(UserIntegral.UIid == userintegral.UIid).first()
            ui_instance.update({"UItrue": 1})
            us_instance = User.query.filter(User.USid == user.id).first()
            usintegral = int(us_instance.USintegral or 0) + int(pointtask.PTnumber or 0)
            us_instance.update({"USintegral": usintegral})
            db.session.add(ui_instance)
            db.session.add(us_instance)

        return Success(message="领取成功")
