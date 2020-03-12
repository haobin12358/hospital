"""
本文件用于处理后台管理员及管理员操作行为
create user: haobin12358
last update time:2020/3/12 15:39
"""
import uuid
from flask import request, current_app
from hospital.extensions.token_handler import admin_required
from hospital.extensions.register_ext import db
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.models.config import Banner

class CAdmin:

    #@token_required
    def add_admin_by_superadmin(self):
        """超级管理员添加普通管理"""

        superadmin = self.get_admin_by_id(request.user.id)
        if not is_hign_level_admin() or \
                superadmin.ADlevel != AdminLevel.super_admin.value or \
                superadmin.ADstatus != AdminStatus.normal.value:
            raise AuthorityError('当前非超管权限')

        data = request.json
        gennerc_log("add admin data is %s" % data)
        parameter_required(('adname', 'adpassword', 'adtelphone'))
        adid = str(uuid.uuid1())
        password = data.get('adpassword')
        # 密码校验
        self.__check_password(password)

        adname = data.get('adname')
        adlevel = getattr(AdminLevel, data.get('adlevel', ''))
        adlevel = 2 if not adlevel else int(adlevel.value)
        header = data.get('adheader') or GithubAvatarGenerator().save_avatar(adid)
        # 等级校验
        if adlevel not in [1, 2, 3]:
            raise ParamsError('adlevel参数错误')

        # 账户名校验
        self.__check_adname(adname, adid)
        adnum = self.__get_adnum()
        # 创建管理员
        adinstance = Admin.create({
            'ADid': adid,
            'ADnum': adnum,
            'ADname': adname,
            'ADtelphone': data.get('adtelphone'),
            'ADfirstpwd': password,
            'ADfirstname': adname,
            'ADpassword': generate_password_hash(password),
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

    def admin_login(self):
        """管理员登录"""
        data = parameter_required(('adname', 'adpassword'))
        admin = self.get_admin_by_name(data.get('adname'))

        # 密码验证
        if admin and check_password_hash(admin.ADpassword, data.get("adpassword")):
            gennerc_log('管理员登录成功 %s' % admin.ADname)
            # 创建管理员登录记录
            ul_instance = UserLoginTime.create({
                "ULTid": str(uuid.uuid1()),
                "USid": admin.ADid,
                "USTip": request.remote_addr,
                "ULtype": UserLoginTimetype.admin.value,
                "UserAgent": request.user_agent.string
            })
            db.session.add(ul_instance)
            token = usid_to_token(admin.ADid, 'Admin', admin.ADlevel, username=admin.ADname)
            admin.fields = ['ADname', 'ADheader', 'ADlevel']

            admin.fill('adlevel', AdminLevel(admin.ADlevel).zh_value)
            admin.fill('adstatus', AdminStatus(admin.ADstatus).zh_value)

            return Success('登录成功', data={'token': token, "admin": admin})
        return ParamsError("用户名或密码错误")