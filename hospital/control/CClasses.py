"""
本文件用于处理课程及课程预约相关逻辑处理
create user: haobin12358
last update time:2020/3/20 12:23
"""
import uuid
import datetime
from flask import request, current_app
from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.register_ext import db
from hospital.extensions.interface.user_interface import is_doctor, is_hign_level_admin, is_admin
from hospital.extensions.success_response import Success
from hospital.extensions.request_handler import token_to_user_
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.error_response import ParamsError, AuthorityError, UserInfoError, CourseStatusError
from hospital.models.departments import Doctor, Departments
from hospital.models.classes import Classes, Course, Subscribe
from hospital.models.user import User
from hospital.config.enums import CourseStatus


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
        if request.args.get('clname'):
            filter_args.append(Classes.CLname.like("%{0}%".format(request.args.get('clname'))))
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
        # 时间控制
        start_time = datetime.datetime.strptime(data.get('costarttime'), "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(data.get('coendtime'), "%Y-%m-%d %H:%M:%S")
        if start_time.date() != end_time.date():
            return {
                "status": 405,
                "status_code": 405301,
                "message": "课程开始结束时间需要同一天"
            }
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
                # 判断课程排班状态和已报名人数，已开始/已结束或者存在报名人员不可修改
                course = Course.query.filter(Course.COid == coid).first()
                if course["COstatus"] != 101:
                    return AuthorityError("无权限")
                subscribe = Subscribe.query.filter(Subscribe.COid == coid).all()
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
        if not is_doctor():
            return AuthorityError("无权限")

        with db.auto_commit():
            for course in request.json:
                course_id = course["coid"]
                co_dict = {
                    "isdelete": 1
                }
                co_instance = Course.query.filter(Course.COid == course_id).first_('未找到该课程排班信息')
                if co_instance["COstatus"] != 101:
                    return AuthorityError("无权限")
                subscribe = Subscribe.query.filter(Subscribe.COid == course_id).all()
                if subscribe:
                    return AuthorityError("已有人报名，不可修改")
                co_instance.update(co_dict, null='not')
                db.session.add(co_instance)
        return Success(message='删除成功')

    def get_course(self):
        """
        获取课程排班列表
        """
        filter_args = [Course.isdelete == 0]
        if request.args.get('doid') or is_doctor():
            if request.args.get('doid'):
                filter_args.append(Course.DOid == request.args.get('doid'))
            else:
                filter_args.append(Course.DOid == token_to_user_(request.args.token).id)
        if request.args.get('clname'):
            filter_args.append(Course.CLname == request.args.get('clname'))
        if request.args.get('costatus'):
            filter_args.append(Course.COstatus == int(request.args.get('costatus')))
        if request.args.get('costarttime'):
            filter_args.append(
                Course.COstarttime > datetime.datetime.strptime(request.args.get('costarttime'), "%Y-%m-%d %H:%M:%S"))
        if request.args.get('coendtime'):
            filter_args.append(
                Course.COendtime < datetime.datetime.strptime(request.args.get('coendtime'), "%Y-%m-%d %H:%M:%S"))
        course_list = Course.query.filter(*filter_args).order_by(Course.createtime.desc()).all_with_page()
        for course in course_list:
            course.fill("costatus_zh", CourseStatus(int(course["COstatus"])).zh_value)
        return Success(message='获取课程排班列表成功', data=course_list)

    def get_course_by_doctor_month(self):
        """
        基于医生id获取未来30天课程情况
        """
        args = parameter_required(('doid', ))
        filter_args = [Course.isdelete == 0, Course.DOid == args.get('doid')]
        year = int(datetime.datetime.now().year)
        month = int(datetime.datetime.now().month)
        day = int(datetime.datetime.now().day)
        start_time = datetime.datetime(year, month, day, 0, 0, 0)
        end_time = datetime.datetime(year, month, day, 23, 59, 59) + datetime.timedelta(days=30)
        filter_args.append(Course.COstarttime > start_time)
        filter_args.append(Course.COendtime < end_time)
        course_list = Course.query.filter(*filter_args).all()
        time_dict = []
        for course in course_list:
            costarttime = course["COstarttime"]
            if "{0}-{1}-{2}".format(year, month, costarttime.day) not in time_dict:
                time_dict.append("{0}-{1}-{2}".format(year, month, costarttime.day))
        return Success(message="获取日期成功", data=time_dict)

    def get_course_by_doctor_day(self):
        """
        基于医生id+日期获取课程安排情况（上午/下午），需要返回是否满员情况
        """
        args = parameter_required(('doid', 'date'))
        date = datetime.datetime.strptime(args.get("date"), "%Y-%m-%d")
        year = int(date.year)
        month = int(date.month)
        day = int(date.day)
        start_time = datetime.datetime(year, month, day, 0, 0, 0)
        end_time = datetime.datetime(year, month, day, 23, 59, 59) + datetime.timedelta(days=7)
        filter_args = [Course.isdelete == 0, Course.DOid == args.get('doid')]
        filter_args.append(Course.COstarttime > start_time)
        filter_args.append(Course.COendtime < end_time)
        course_list = Course.query.filter(*filter_args).order_by(Course.COstarttime).all()
        time_dict = []
        for course in course_list:
            costarttime = course["COstarttime"]
            coid = course["COid"]
            subscribe = Subscribe.query.filter(Subscribe.isdelete == 0, Subscribe.COid == coid).all()
            conum = course["COnum"]
            if costarttime.hour < 12:
                ampm = "am"
            else:
                ampm = "pm"
            time_not_full = {
                "ampm": ampm,
                "date": "{0}-{1}-{2}".format(year, month, costarttime.day),
                "is_full": 0
            }
            time_is_full = {
                "ampm": ampm,
                "date": "{0}-{1}-{2}".format(year, month, costarttime.day),
                "is_full": 1
            }
            if len(subscribe) < conum:
                if time_not_full not in time_dict:
                    time_dict.append(time_not_full)
                    if time_is_full in time_dict:
                        time_dict.remove(time_is_full)

            elif len(subscribe) == conum:
                if time_not_full not in time_dict and time_is_full not in time_dict:
                    time_dict.append(time_is_full)


        return Success(message="获取课程情况成功", data=time_dict)

    def get_course_by_doctor_ampm(self):
        """
        基于医生id+日期+上下午标识符获取课程安排情况
        """
        args = parameter_required(("doid", "date", "ampm"))
        date = datetime.datetime.strptime(args.get("date"), "%Y-%m-%d")
        year = int(date.year)
        month = int(date.month)
        day = int(date.day)
        if args.get("ampm") == "am":
            start_time = datetime.datetime(year, month, day, 0, 0, 0)
            end_time = datetime.datetime(year, month, day, 11, 59, 59)
        else:
            start_time = datetime.datetime(year, month, day, 12, 0, 0)
            end_time = datetime.datetime(year, month, day, 23, 59, 59)
        filter_args = [Course.isdelete == 0, Course.DOid == args.get('doid')]
        print(1)
        filter_args.append(Course.COstarttime > start_time)
        filter_args.append(Course.COendtime < end_time)
        course_list = Course.query.filter(*filter_args).order_by(Course.COstarttime).all()
        for course in course_list:
            coid = course["COid"]
            subscribe = Subscribe.query.filter(Subscribe.isdelete == 0, Subscribe.COid == coid).all()
            course.fill("subnum", len(subscribe))
            course.fill("date", args.get("date"))
        return Success(message="获取具体安排成功", data=course_list)

    def subscribe_classes(self):
        """
        预约具体课程
        """
        args = request.args.to_dict()

        data = parameter_required(('coid', ))
        course = Course.query.filter(Course.COid == data.get('coid')).first_("未找到课程信息")
        # 判断是否可报名
        if course["COstatus"] != 101:
            return CourseStatusError()
        user_id = token_to_user_(args.get("token")).id
        user = User.query.filter(User.USid == user_id).first_("未找到用户信息")
        print(user)
        # TODO 需要查看用户是否有对应的课时余额
        if "UStelphone" not in user.keys() or not user["UStelphone"]:
            return UserInfoError()
        su_dict = {
            "SUid": str(uuid.uuid1()),
            "COid": data.get("coid"),
            "CLname": course["CLname"],
            "COstarttime": course["COstarttime"],
            "DOname": course["DOname"],
            "USname": user["USname"],
            "USid": user_id,
            "UStelphone": user["UStelphone"],
            "SUstatus": 201
        }
        with db.auto_commit():
            su_instance = Subscribe.create(su_dict)
            db.session.add(su_instance)

        return Success("预约成功")
