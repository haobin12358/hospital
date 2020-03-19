"""
本文件用于处理后台管理员及管理员操作行为
create user: haobin12358
last update time:2020/3/13 03:53
"""
import uuid, re
from flask import request, current_app
from hospital.extensions.token_handler import usid_to_token
from hospital.extensions.interface.user_interface import admin_required, is_hign_level_admin
from hospital.extensions.register_ext import db
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.request_handler import token_to_user_
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, AuthorityError
from werkzeug.security import check_password_hash, generate_password_hash
from hospital.models.admin import Admin, AdminActions
from hospital.models.departments import Doctor
from hospital.config.enums import AdminLevel, AdminStatus

class CAdmin:

    @admin_required
    def add_admin(self):
        """超级管理员添加普通管理"""
        if not is_hign_level_admin():
            return AuthorityError()

        data = parameter_required(('adname',))
        adid = str(uuid.uuid1())

        adname = data.get('adname')
        adlevel = 2

        # 账户名校验
        self.__check_adname(adname)
        # 创建管理员
        with db.auto_commit():
            adinstance = Admin.create({
                'ADid': adid,
                'ADname': adname,
                "ADtelphone": "",
                'ADpassword': generate_password_hash("123456"),
                'ADheader': "",
                'ADlevel': adlevel,
                'ADstatus': 0,
            })
            db.session.add(adinstance)

            # 创建管理员变更记录
            an_instance = AdminActions.create({
                'AAid': str(uuid.uuid1()),
                'ADid': "1",
                "AAaction": 1,
                "AAmodel": "Admin",
                'AAdetail': str(data)
            })

            db.session.add(an_instance)
        return Success('创建管理员成功')

    def __check_password(self, password):
        """
        校检密码
        """
        if not password or len(password) < 4:
            raise ParamsError('密码长度低于4位')
        zh_pattern = re.compile(r'[\u4e00-\u9fa5]+')
        match = zh_pattern.search(password)
        if match:
            raise ParamsError(u'密码包含中文字符')
        return True

    def __check_adname(self, adname):
        """账户名校验"""
        if not adname:
            return True
        suexist = Admin.query.filter(Admin.isdelete == 0, Admin.ADname == adname).first()
        if suexist:
            raise ParamsError('用户名已存在')
        return True

    def admin_login(self):
        """管理员登录"""
        data = parameter_required(('adname', 'adpassword', 'adtype'))
        if data['adtype'] == 1:
            # 管理员/超级管理员登录
            ad = Admin.query.filter(Admin.isdelete == 0,
                                    Admin.ADname == data.get("adname")).first()

            # 密码验证
            if ad and check_password_hash(ad.ADpassword, data.get("adpassword")):
                token = usid_to_token(ad.ADid, 'Admin', ad.ADlevel, username=ad.ADname)
                ad.fields = ['ADname', 'ADheader', 'ADlevel']

                ad.fill('adlevel', AdminLevel(ad.ADlevel).zh_value)
                ad.fill('adstatus', AdminStatus(ad.ADstatus).zh_value)
                with db.auto_commit():
                    an_instance = AdminActions.create({
                        'AAid': str(uuid.uuid1()),
                        'ADid': ad.ADid,
                        "AAaction": 4,
                        "AAmodel": "Admin",
                        'AAdetail': str(data)
                    })

                    db.session.add(an_instance)
                return Success('登录成功', data={'token': token, "admin": ad})
        elif data['adtype'] == 2:
            # 医生登录
            dc = Doctor.query.filter(Doctor.isdelete == 0, Doctor.DOtel == data.get('adname')).first()
            print(dc.DOpassword)
            print(generate_password_hash('635698'))
            if dc and check_password_hash(dc.DOpassword, data.get('adpassword')):
                token = usid_to_token(dc.DOid, 'Doctor', 3, username=dc.DOname)
                with db.auto_commit():
                    an_instance = AdminActions.create({
                        'AAid': str(uuid.uuid1()),
                        'ADid': dc.DOid,
                        "AAaction": 4,
                        "AAmodel": "Doctor",
                        'AAdetail': str(data)
                    })

                    db.session.add(an_instance)
                return Success('登录成功', data={'token': token, 'admin': dc})
            # TODO 需要增加登录时间

        return ParamsError("用户名或密码错误")

    def update_admin_password(self):
        """更新管理员密码"""
        data = parameter_required(('password_old', 'password_new', 'password_repeat'))

        # 校检两次密码是否相同
        pwd_new = data.get('password_new')
        pwd_old = data.get('password_old')
        pwd_repeat = data.get('password_repeat')
        if pwd_new != pwd_repeat:
            raise ParamsError('两次输入的密码不同')
        token = token_to_user_(request.args.get("token"))
        if int(request.args.get('adtype')) == 1:
            ad = Admin.query.filter(Admin.isdelete == 0, Admin.ADid == token.id).first()
            adpassword = ad.ADpassword
            ad_dict = {
                "ADpassword": generate_password_hash(pwd_new)
            }
        elif int(request.args.get('adtype')) == 2:
            ad = Doctor.query.filter(Doctor.isdelete == 0, Doctor.DOid == token.id).first()
            print(ad)
            adpassword = ad.DOpassword
            ad_dict = {
                "DOpassword": generate_password_hash(pwd_new)
            }
        else:
            ad = None
            adpassword = None
            ad_dict = {}
        if ad:
            with db.auto_commit():
                if check_password_hash(adpassword, pwd_old):
                    print(1)
                    self.__check_password(pwd_new)
                    ad.ADpassword = generate_password_hash(pwd_new)
                    ad.update(ad_dict, null='not')
                else:
                    raise ParamsError('旧密码有误')
            db.session.add(ad)
            return Success('更新密码成功')

        raise AuthorityError('账号已被回收')

    @admin_required
    def delete_admin(self):
        """冻结管理员"""
        data = parameter_required(('adid', 'adtype'))

        token = token_to_user_(request.args.get("token"))
        # 权限判断
        ad = Admin.query.filter(Admin.isdelete == 0, Admin.ADid == token.id).first()
        adid = ad.ADid
        if adid != "1":
            raise AuthorityError("无权限")
        else:
            with db.auto_commit():
                ad_dict = {
                    "isdelete": 1
                }
                if data['adtype'] == 1:
                    ad_instance = Admin.query.filter_by(Admin.ADid == data.get("adid"), Admin.isdelete == 0)\
                        .first_('未找到该账号信息')
                    ad_instance.update(ad_dict, null='not')
                elif data['adtype'] == 2:
                    ad_instance = Doctor.query.filter_by(Doctor.DOid == data.get('adid'), Doctor.isdelete == 0)\
                        .first_('未找到该账号信息')
                    ad_instance.update(ad_dict, null='not')
            db.session.add(ad_instance)
            msg = "删除账号成功"
        return Success(message=msg)

    @admin_required
    def reset_password(self):
        """重置管理员密码"""
        data = parameter_required(('adid', 'adtype'))
        token = token_to_user_(request.args.get('token'))
        # 判断权限
        ad = Admin.query.filter(Admin.isdelete == 0, Admin.ADid == token.id).first()
        adid = ad.ADid
        if adid != "1":
            raise AuthorityError("无权限")
        else:
            with db.auto_commit():
                if data['adtype'] == 1:
                    ad_dict = {
                        'ADpassword': generate_password_hash('123456')
                    }
                    ad_instance = Admin.query.filter(Admin.ADid == data.get("adid"), Admin.isdelete == 0)\
                        .first_('未找到该账号信息')
                    ad_instance.update(ad_dict, null='not')
                elif data['adtype'] == 2:
                    ad_instance = Doctor.query.filter(Doctor.DOid == data.get('adid'), Doctor.isdelete == 0)\
                        .first_('未找到该账号信息')
                    ad_dict = {
                        'DOpassword': generate_password_hash(str(ad_instance.DOtel)[-6:])
                    }
                    ad_instance.update(ad_dict, null='not')
            db.session.add(ad_instance)
            msg = "重置密码成功"
        return Success(message=msg)

    @admin_required
    def get_admin_list(self):
        """管理员列表"""
        token = token_to_user_(request.args.get('token'))
        # 判断权限
        ad = Admin.query.filter(Admin.isdelete == 0, Admin.ADid == token.id).first()
        adid = ad.ADid
        if adid != "1":
            raise AuthorityError("无权限")
        else:
            ad_list = Admin.query.filter(Admin.isdelete == 0, Admin.ADlevel == 2)\
                .order_by(Admin.createtime.desc()).all()
            admin_list = []
            for admin in ad_list:
                admin_dict = {}
                admin_dict['adid'] = admin.ADid
                admin_dict['adname'] = admin.ADname
                admin_dict['adtype'] = 1
                admin_dict['adtype_zh'] = '管理员'
                action = AdminActions.query.filter(AdminActions.ADid == admin.ADid, AdminActions.AAaction == 4,
                                                   AdminActions.AAmodel == 'Admin')\
                    .order_by(AdminActions.createtime.desc()).first()
                if action:
                    admin_dict['adlogin_last'] = action['createtime']
                else:
                    admin_dict['adlogin_last'] = None
                admin_list.append(admin_dict)
            dc_list = Doctor.query.filter(Doctor.isdelete == 0).order_by(Doctor.createtime.desc()).all()
            for doctor in dc_list:
                admin_dict = {}
                admin_dict['adid'] = doctor.DOid
                admin_dict['adname'] = doctor.DOtel
                admin_dict['adtype'] = 2
                admin_dict['adtype_zh'] = '医生'
                action = AdminActions.query.filter(AdminActions.ADid == doctor.DOid, AdminActions.AAaction == 4,
                                                   AdminActions.AAmodel == 'Doctor') \
                    .order_by(AdminActions.createtime.desc()).first()
                if action:
                    admin_dict['adlogin_last'] = action['createtime']
                else:
                    admin_dict['adlogin_last'] = None
                admin_list.append(admin_dict)
            start_num = int(int(request.args.get('page_num')) - 1) * int(request.args.get('page_size') or 10)
            end_num = int(request.args.get('page_num')) * int(request.args.get('page_size') or 10)
            if len(admin_list) % int(request.args.get('page_size') or 10) == 0:
                total_page = int(len(admin_list) / int(request.args.get('page_size') or 10))
            else:
                total_page = int(len(admin_list) / int(request.args.get('page_size') or 10)) + 1
            return {
                "status": 200,
                "message": "获取管理员列表成功",
                "data": admin_list[start_num: end_num],
                "total_page": total_page,
                "total_size": len(admin_list)
            }