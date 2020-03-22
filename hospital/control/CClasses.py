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
from hospital.extensions.request_handler import token_to_user_
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
        filter_args = [Classes.isdelete == 0]
        if request.args.get('deid'):
            filter_args.append(Classes.DEid == request.args.get('deid'))
        classes = Classes.query.filter(*filter_args)\
            .order_by(Classes.CLindex.asc(), Classes.updatetime.desc()).all_with_page()

        return Success(message="获取课程列表成功", data=classes)

    def get(self):
        """
        课程详情
        """
        args = parameter_required(('clid'))
        classes = Classes.query.filter(Classes.isdelete == 0, Classes.CLid == args.get('clid')).first_("未查到课程信息")
        return Success(message="获取课程信息成功", data=classes)

    def set_course(self):
        """
        课程排班
        """
        if not is_doctor():
            return AuthorityError('无权限')
        data = parameter_required(('clid', 'costarttime', 'coendtime', 'conum'))
        coid = data.get('coid')
        classes = Classes.query.filter(Classes.CLid == data.get('clid')).first_("未找到课程信息，请联系管理员")
        token = token_to_user_(request.args.get("token"))
        doctor = Doctor.query.filter(Doctor.DOid == token.id, Doctor.isdelete == 0).first()
        # TODO 时间控制

        co_dict = {
            "CLid": data.get("clid"),
            "CLname": classes["CLname"],
            "DOid": token.id,
            "DOname": doctor["DOname"],
            "COstarttime": data.get("costarttime"),
            "COendtime": data.get("coendtime"),
            "COnum": data.get("conum"),
            "COstatus": 101
        }
        with db.auto_commit():
            if not coid:
                co_dict["COid"] = str(uuid.uuid1())
                co_instance = Course.create(co_dict)
                msg = "创建成功"
            else:
                # TODO 判断课程排班状态和已报名人数，已开始/已结束或者存在报名人员不可修改
                course = Course.query.filter(Course.COid).first()
                if course["COstatus"] != 101:
                    return AuthorityError("无权限")
                subscribe = Subscribe.query.filter(Classes.COid).all()
                if subscribe:
                    return AuthorityError("已有人报名，不可修改")
                co_instance = Classes.query.filter_by_(COid=coid).first_('未找到该课程排班信息')

                co_instance.update(co_dict, null='not')
                msg = '编辑成功'
            db.session.add(co_instance)
        return Success(message=msg, data={"coid": co_instance.COid})

    def delete_course(self):
        """
        删除课程排班
        """
        return

    def get_course(self):
        """
        获取课程排班列表
        """
        filter_args = []
