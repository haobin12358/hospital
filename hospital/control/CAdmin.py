"""
本文件用于处理后台管理员及管理员操作行为
create user: haobin12358
last update time:2020/3/12 15:39
"""
import uuid, re
from flask import request, current_app
from hospital.extensions.token_handler import usid_to_token
from hospital.extensions.interface.user_interface import admin_required, is_hign_level_admin
from hospital.extensions.register_ext import db
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, AuthorityError
from werkzeug.security import check_password_hash, generate_password_hash
from hospital.models.admin import Admin, AdminActions
from hospital.config.enums import AdminLevel, AdminStatus

class CAdmin:

    @admin_required
    def add_admin(self):
        """超级管理员添加普通管理"""
        print(is_hign_level_admin())
        if not is_hign_level_admin():
            return AuthorityError()

        data = parameter_required(('adname',))
        adid = str(uuid.uuid1())

        adname = data.get('adname')
        adlevel = 2

        # 账户名校验
        self.__check_adname(adname)
        adnum = self.__get_adnum()
        # 创建管理员
        adinstance = Admin.create({
            'ADid': adid,
            'ADnum': adnum,
            'ADname': adname,
            'ADtelphone': data.get('adtelphone'),
            'ADfirstpwd': "123456",
            'ADfirstname': adname,
            'ADpassword': generate_password_hash("123456"),
            'ADheader': header,
            'ADlevel': adlevel,
            'ADstatus': 0,
        })
        db.session.add(adinstance)

        # 创建管理员变更记录
        an_instance = AdminNotes.create({
            'ANid': str(uuid.uuid1()),
            'ADid': adid,
            'ANaction': '{0} 创建管理员{1} 等级{2}'.format(superadmin.ADname, adname, adlevel),
            "ANdoneid": request.user.id
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
                                Admin.ADlevel == 1,
                                Admin.ADfirstname == data.get("adname")).first()

        # 密码验证
        if ad and check_password_hash(ad.ADpassword, data.get("adpassword")):
            token = usid_to_token(ad.ADid, 'Admin', ad.ADlevel, username=ad.ADname)
            ad.fields = ['ADname', 'ADheader', 'ADlevel']

            ad.fill('adlevel', AdminLevel(ad.ADlevel).zh_value)
            ad.fill('adstatus', AdminStatus(ad.ADstatus).zh_value)

            return Success('登录成功', data={'token': token, "admin": ad})
        return ParamsError("用户名或密码错误")