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
        data = parameter_required(('adname', 'adpassword'))
        ad = Admin.query.filter(Admin.isdelete == 0,
                                Admin.ADname == data.get("adname")).first()

        # 密码验证
        if ad and check_password_hash(ad.ADpassword, data.get("adpassword")):
            token = usid_to_token(ad.ADid, 'Admin', ad.ADlevel, username=ad.ADname)
            ad.fields = ['ADname', 'ADheader', 'ADlevel']

            ad.fill('adlevel', AdminLevel(ad.ADlevel).zh_value)
            ad.fill('adstatus', AdminStatus(ad.ADstatus).zh_value)

            return Success('登录成功', data={'token': token, "admin": ad})
        return ParamsError("用户名或密码错误")

    @admin_required
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
        ad = Admin.query.filter(Admin.isdelete == 0, Admin.ADid == token.id).first()
        adid = ad.ADid
        ad_dict = {
            "ADpassword": ad.ADpassword
        }
        if ad:
            with db.auto_commit():

                ad_instance = Admin.query.filter_by_(ADid=adid).first_('未找到该账号信息')
                print(ad_instance)
                if check_password_hash(ad.ADpassword, pwd_old):
                    self.__check_password(pwd_new)
                    ad.ADpassword = generate_password_hash(pwd_new)
                    ad_instance.update(ad_dict, null='not')
                else:
                    raise ParamsError('旧密码有误')
            db.session.add(ad_instance)
            return Success('更新密码成功')

        raise AuthorityError('账号已被回收')

    @admin_required
    def delete_admin(self):
        """冻结管理员"""
        data = parameter_required(('adid',))

        token = token_to_user_(request.args.get("token"))
        # 权限判断
        ad = Admin.query.filter(Admin.isdelete == 0, Admin.ADid == token.id).first()
        adid = ad.ADid
        print(adid)
        if adid != "1":
            raise AuthorityError("无权限")
        else:
            with db.auto_commit():
                ad_dict = {
                    "isdelete": 1
                }
                ad_instance = Admin.query.filter_by_(ADid=data.get("adid")).first_('未找到该账号信息')
                ad_instance.update(ad_dict, null='not')
            db.session.add(ad_instance)
            msg = "删除账号成功"
        return Success(message=msg)