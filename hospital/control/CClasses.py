"""
本文件用于处理课程及课程预约相关逻辑处理
create user: haobin12358
last update time:2020/3/20 12:23
"""
import uuid
from flask import request, current_app
from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.register_ext import db
from hospital.extensions.interface.user_interface import is_doctor, is_hign_level_admin, is_admin
from hospital.extensions.success_response import Success
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.error_response import ParamsError, AuthorityError
from hospital.models.departments import Doctor, Departments
from hospital.models.classes import Classes, Course, Subscribe
from hospital.models.user import User


class CClasses:

    def set_class(self):
        """
        创建/编辑/删除课程
        """
        if not (is_admin() or is_hign_level_admin()):
            return AuthorityError('无权限')
        data = parameter_required(('clname', "clpicture", "deid", "clintroduction"))
        clid = data.get('clid')
        department = Departments.query.filter(Departments.DEid == data.get("deid")).first_("未找到科室信息")
        cl_dict = {'CLname': data.get('clname'),
                   'CLpicture': data.get('clpicture'),
                   'DEid': data.get('deid'),
                   'DEname': department['DEname'],
                   'CLintroduction': data.get('clintroduction')}
        with db.auto_commit():
            if not clid:
                """新增"""
                cl_dict['CLid'] = str(uuid.uuid1())
                cl_instance = Classes.create(cl_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                cl_instance = Classes.query.filter_by_(CLid=clid).first_('未找到该轮播图信息')
                if data.get('delete'):
                    cl_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    cl_instance.update(cl_dict, null='not')
                    msg = '编辑成功'
            db.session.add(cl_instance)
        return Success(message=msg, data={'clid': cl_instance.CLid})

    def list(self):
        """
        课程列表
        """
        department = Departments.query.filter(Departments.isdelete == 0).with_entities(Departments.DEid, Departments.D).first_("未找到科室信息")
