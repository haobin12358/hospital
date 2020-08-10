"""
本文件用于处理课程及课程预约相关逻辑处理
create user: haobin12358
last update time:2020/3/20 12:23
"""
import uuid
import datetime
from flask import request, current_app
from decimal import Decimal
from hospital.extensions.register_ext import db
from hospital.extensions.interface.user_interface import is_doctor, is_hign_level_admin, is_admin, is_user, \
    token_required, doctor_required
from hospital.extensions.success_response import Success
from hospital.extensions.request_handler import token_to_user_
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.error_response import PoorScore, AuthorityError, UserInfoError, CourseStatusError, ParamsError
from hospital.extensions.tasks import add_async_task, change_course_status, cancel_async_task
from hospital.models.departments import Doctor, Departments, DoctorMedia
from hospital.models.classes import Classes, Course, Subscribe, Setmeal
from hospital.models.user import User, UserHour
from hospital.config.enums import CourseStatus, SubscribeStatus
from hospital.models.review import Review
from hospital.models.register import Register


class CClasses:

    @token_required
    def set_class(self):
        """
        创建/编辑/删除课程
        """
        if not (is_admin() or is_hign_level_admin()):
            return AuthorityError('无权限')
        data = parameter_required(('clname', "clpicture", "deid", "clintroduction", "clprice")
                                  if not request.json.get('delete') else('clid',))
        clid = data.get('clid')
        if clid:
            classes = Classes.query.filter(Classes.CLid == clid).first_("未找到课程信息")
            department = Departments.query.filter(Departments.DEid == classes.DEid).first_("未找到科室信息")
        else:
            department = Departments.query.filter(Departments.DEid == data.get("deid")).first_("未找到科室信息")
        cl_dict = {'CLname': data.get('clname'),
                   'CLpicture': data.get('clpicture'),
                   'DEid': data.get('deid'),
                   'DEname': department['DEname'],
                   'CLintroduction': data.get('clintroduction'),
                   'CLprice': data.get('clprice')}
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
        if is_user():
            doctor_list2 = []
            doctor_list = Course.query.with_entities(Course.DOid).distinct().all_with_page()
            for doctor in doctor_list:
                doid = doctor.DOid
                doctor_dict = Doctor.query.filter(Doctor.DOid == doid, Doctor.isdelete == 0).first_("未找到医生信息")
                doctor = doctor_dict
                doctor_media = DoctorMedia.query.filter(DoctorMedia.isdelete == 0, DoctorMedia.DMtype == 0,
                                                        DoctorMedia.DOid == doid).first()
                doctor.fill("doctormainpic", doctor_media["DMmedia"]) # 医生主图
                department = Departments.query.filter(Departments.isdelete == 0,
                                                      Departments.DEid == doctor["DEid"])\
                    .first_("未找到科室信息")
                doctor.fill("dename", department["DEname"]) # 科室名称
                review_good = Review.query.filter(Review.isdelete == 0, Review.RVnum >= 4, Review.DOid == doid).all()
                review = Review.query.filter(Review.isdelete == 0, Review.DOid == doid).all()
                if len(review) == 0:
                    # 无评论情况下默认100%好评率
                    review_percentage = 1
                else:
                    review_percentage = Decimal(str(int(len(review_good) / len(review) or 0)))
                doctor.fill("favorablerate", "{0}%".format(review_percentage * 100)) # 好评率
                register = Register.query.filter(Register.DOid == doid, Register.isdelete == 0).all()
                doctor.fill("treatnum", len(register)) # 接诊次数
                doctor_list2.append(doctor)
            classes.fill("doctor_list", doctor_list2)
        return Success(message="获取课程信息成功", data=classes)

    def set_course(self):
        """
        课程排班
        """
        if not is_doctor():
            return AuthorityError('排班需医生账号操作')
        data = parameter_required(('clid', 'costarttime', 'coendtime', 'conum'))
        coid = data.get('coid')
        classes = Classes.query.filter(Classes.CLid == data.get('clid')).first_("未找到课程信息，请联系管理员")
        doctor = Doctor.query.filter(Doctor.DOid == request.user.id, Doctor.isdelete == 0).first()
        # 时间控制
        start_time = datetime.datetime.strptime(data.get('costarttime'), "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(data.get('coendtime'), "%Y-%m-%d %H:%M:%S")
        if not (end_time > start_time > datetime.datetime.now()):
            raise ParamsError('课程结束时间要大于开始时间, 开始时间要大于当前时间')
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

                # 添加开始异步任务
                add_async_task(func=change_course_status, start_time=start_time,
                               func_args=(co_dict["COid"],), conn_id='start_course{}'.format(co_dict["COid"]))
                # 添加结束异步任务
                add_async_task(func=change_course_status, start_time=end_time,
                               func_args=(co_dict["COid"], True), conn_id='end_course{}'.format(co_dict["COid"]))
            else:
                # 判断课程排班状态和已报名人数，已开始/已结束或者存在报名人员不可修改
                course = Course.query.filter(Course.COid == coid).first()
                if course["COstatus"] != 101:
                    return AuthorityError("无权限")
                subscribe = Subscribe.query.filter(Subscribe.COid == coid).all()
                if subscribe:
                    return AuthorityError("已有人报名，不可修改")
                co_instance = Course.query.filter(Course.COid == coid).first_('未找到该课程排班信息')
                co_instance.update(co_dict, null='not')
                msg = '编辑成功'

                cancel_async_task(conn_id='start_course{}'.format(co_instance.COid))  # 取消已有的开始时间异步任务
                cancel_async_task(conn_id='end_course{}'.format(co_instance.COid))  # 取消已有的结束时间异步任务
                # 重新添加开始异步任务
                add_async_task(func=change_course_status, start_time=start_time,
                               func_args=(co_instance.COid,), conn_id='start_course{}'.format(co_instance.COid))
                # 重新添加结束异步任务
                add_async_task(func=change_course_status, start_time=end_time,
                               func_args=(co_instance.COid, True), conn_id='end_course{}'.format(co_instance.COid))
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

                cancel_async_task(conn_id='start_course{}'.format(co_instance.COid))  # 取消已有的开始时间异步任务
                cancel_async_task(conn_id='end_course{}'.format(co_instance.COid))  # 取消已有的结束时间异步任务

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
                filter_args.append(Course.DOid == token_to_user_(request.args.get('token')).id)
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
        args = parameter_required(('doid', 'clid'))
        filter_args = [Course.isdelete == 0, Course.DOid == args.get('doid'), Course.CLid == args.get('clid')]
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
        args = parameter_required(('doid', 'date', 'clid'))
        date = datetime.datetime.strptime(args.get("date"), "%Y-%m-%d")
        year = int(date.year)
        month = int(date.month)
        day = int(date.day)
        start_time = datetime.datetime(year, month, day, 0, 0, 0)
        end_time = datetime.datetime(year, month, day, 23, 59, 59) + datetime.timedelta(days=7)
        filter_args = [Course.isdelete == 0, Course.DOid == args.get('doid'), Course.CLid == args.get('clid')]
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
        args = parameter_required(("doid", "date", "ampm", 'clid'))
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
        filter_args = [Course.isdelete == 0, Course.DOid == args.get('doid'), Course.CLid == args.get('clid')]

        filter_args.append(Course.COstarttime > start_time)
        filter_args.append(Course.COendtime < end_time)
        course_list = Course.query.filter(*filter_args).order_by(Course.COstarttime).all()
        data = {}
        for course in course_list:
            data["date"] = args.get("date")
            data["clname"] = course.CLname
            data["doname"] = course.DOname
            coid = course["COid"]
            time_zones = "{0}:{1}-{2}:{3}".format(course.COstarttime.strftime("%H"), course.COstarttime.strftime("%M"),
                                                  course.COendtime.strftime("%H"), course.COendtime.strftime("%M"))
            course.fill("time_zones", time_zones)
            subscribe = Subscribe.query.filter(Subscribe.isdelete == 0, Subscribe.COid == coid).all()
            course.fill("subnum", len(subscribe))
            course.fill("date", args.get("date"))
        data["course_list"] = course_list
        return Success(message="获取具体安排成功", data=data)

    @token_required
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
        user_id = getattr(request, 'user').id
        user = User.query.filter(User.USid == user_id).first_("未找到用户信息")
        print(user)
        # 查看用户是否有对应的课时余额
        userhour_list = UserHour.query.filter(UserHour.USid == user_id, UserHour.isdelete == 0,
                                         UserHour.CLid == course.CLid).all()
        uhnum = 0
        for userhour in userhour_list:
            uhnum += userhour.UHnum
        if uhnum <= 0:
            return PoorScore()
        if "UStelphone" not in user.keys() or not user["UStelphone"]:
            return UserInfoError()
        su_dict = {
            "SUid": str(uuid.uuid1()),
            "COid": data.get("coid"),
            "CLname": course["CLname"],
            "COstarttime": course["COstarttime"],
            "DOid": course["DOid"],
            "DOname": course["DOname"],
            "USname": user["USname"],
            "USid": user_id,
            "UStelphone": user["UStelphone"],
            "SUstatus": 201
        }
        with db.auto_commit():
            su_instance = Subscribe.create(su_dict)
            db.session.add(su_instance)
            userhour_instance = UserHour.query.filter(UserHour.USid == user_id, UserHour.isdelete == 0,
                                                  UserHour.CLid == course.CLid, UserHour.UHnum > 0).first()
            userhour_dict = {
                "UHid": userhour_instance.UHid,
                "UHnum": userhour_instance.UHnum - 1
            }
            userhour_instance.update(userhour_dict, null="not")
            db.session.add(userhour_instance)

        return Success("预约成功")

    @token_required
    def set_setmeal(self):
        """
        新增/修改/删除课时套餐
        """
        if not (is_admin() or is_hign_level_admin()):
            return AuthorityError('无权限')
        data = parameter_required(('clid', 'smnum', 'smprice') if not request.json.get('delete') else('smid',))
        smid = data.get('smid')
        if smid:
            setmeal = Setmeal.query.filter(Setmeal.SMid == smid).first_("未找到该套餐信息")
            classes = Classes.query.filter(Classes.isdelete == 0,
                                           Classes.CLid == setmeal.CLid).first_("未找到该课程信息")
        else:
            classes = Classes.query.filter(Classes.isdelete == 0,
                                           Classes.CLid == data.get('clid')).first_("未找到该课程信息")
        clname = classes["CLname"]
        sm_dict = {
            "CLid": data.get('clid'),
            "CLname": clname,
            "SMnum": data.get('smnum'),
            "SMprice": data.get('smprice')
        }
        with db.auto_commit():
            if not smid:
                """新增"""
                sm_dict['SMid'] = str(uuid.uuid1())
                sm_instance = Setmeal.create(sm_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                sm_instance = Setmeal.query.filter_by_(SMid=smid).first_('未找到该轮播图信息')
                if data.get('delete'):
                    sm_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    sm_instance.update(sm_dict, null='not')
                    msg = '编辑成功'
            db.session.add(sm_instance)
        return Success(message=msg, data={'smid': sm_instance.SMid})

    @token_required
    def get_setmeal(self):
        """
        获取课时套餐
        """
        if is_admin() or is_hign_level_admin():
            setmeal = Setmeal.query.filter(Setmeal.isdelete == 0).all_with_page()
            return Success(message="获取课时套餐成功", data=setmeal)
        elif is_user():
            args = parameter_required(('clid',))
            classes = Classes.query.filter(Classes.isdelete == 0, Classes.CLid == args.get('clid')).first_("未找到该课程信息")
            setmeal_list = []
            setmeal_list.append({
                "smid": "1",
                "clid": args.get('clid'),
                "clname": classes["CLname"],
                "smnum": 1,
                "smprice": classes["CLprice"]
            })
            setmeal = Setmeal.query.filter(Setmeal.isdelete == 0, Setmeal.CLid == args.get("clid")).all()
            setmeal.sort(key=lambda x: x["SMnum"])
            for setmeal_one in setmeal:
                setmeal_list.append(setmeal_one)
            return Success(message="获取课时套餐成功", data=setmeal_list)

    @token_required
    def get_subscribe_list(self):
        """
        分页获取预约列表
        """
        filter_args = [Subscribe.isdelete == 0]
        args = request.args.to_dict()
        user_id = getattr(request, 'user').id
        if is_user():
            filter_args.append(Subscribe.USid == user_id)
        elif is_doctor():
            filter_args.append(Subscribe.DOid == user_id)
        else:
            pass
        if args.get('sustatus'):
            filter_args.append(Subscribe.SUstatus == int(args.get('sustatus')))
        if args.get('usname'):
            filter_args.append(Subscribe.USname.like("%{0}%".format(args.get('usname'))))
        if args.get('clname'):
            filter_args.append(Subscribe.CLname.like("%{0}%".format(args.get('clname'))))
        if args.get('doname'):
            filter_args.append(Subscribe.DOname.like("%{0}%".format(args.get('doname'))))
        if args.get('codate'):

            filter_args.append(Subscribe.COstarttime.date() ==
                               datetime.datetime.strptime(args.get('codate'), "%Y-%m-%d").date())
        subcribe_list = Subscribe.query.filter(*filter_args).order_by(Subscribe.createtime).all_with_page()
        for subcribe in subcribe_list:
            subcribe.fill("sustatus_zh", SubscribeStatus(int(subcribe["SUstatus"])).zh_value)
            doid = subcribe["DOid"]
            doctor = Doctor.query.filter(Doctor.DOid == doid).first_("未找到该医生信息")
            subcribe.fill('dotitle', doctor.DOtitle)
            docmedia = DoctorMedia.query.filter(DoctorMedia.DOid == doid, DoctorMedia.DMtype == 0,
                                                DoctorMedia.isdelete == 0).first()
            subcribe.fill('doctormainpic', docmedia.DMmedia)
            coid = subcribe["COid"]
            course = Course.query.filter(Course.COid == coid, Course.isdelete == 0).first_("未找到课程排班信息")
            clid = course["CLid"]
            classes = Classes.query.filter(Classes.CLid == clid, Classes.isdelete == 0).first_("未找到课程信息")
            subcribe.fill("dename", classes["DEname"])
            subcribe.fill("createtime", subcribe["createtime"])
            subcribe.fill("coendtime", course["COendtime"])
            if subcribe["COstarttime"].hour < 12:
                subcribe.fill("date", "{0}.{1}.{2}".format(
                    subcribe["COstarttime"].year, subcribe["COstarttime"].month, subcribe["COstarttime"].day))
                subcribe.fill("time", "{0} {1}:{2}-{3}:{4}".format(
                    "上午", subcribe["COstarttime"].hour, subcribe["COstarttime"].minute, subcribe["coendtime"].hour,
                    subcribe["coendtime"].minute))
            else:
                subcribe.fill("date", "{0}.{1}.{2}".format(
                    subcribe["COstarttime"].year, subcribe["COstarttime"].month, subcribe["COstarttime"].day))
                subcribe.fill("time", "{0} {1}:{2}-{3}:{4}".format(
                    "下午", subcribe["COstarttime"].hour - 12, subcribe["COstarttime"].minute,
                    subcribe["coendtime"].hour - 12, subcribe["coendtime"].minute))

        return Success(message="获取预约列表成功", data=subcribe_list)

    @doctor_required
    def update_sustatus(self):
        """
        批量确认已上课
        """

        with db.auto_commit():
            for subcribe in request.json:
                subcribe_id = subcribe["suid"]
                su_dict = {
                    "SUstatus": 202
                }
                su_instance = Subscribe.query.filter(Subscribe.SUid == subcribe_id).first_('未找到该课程预约信息')
                if su_instance["DOid"] != getattr(request, 'user').id:
                    return AuthorityError("无权限")
                su_instance.update(su_dict, null='not')
                db.session.add(su_instance)
        return Success(message='确认成功')
