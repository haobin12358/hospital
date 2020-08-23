# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, date
from flask import current_app, request
from sqlalchemy import cast, Date, func

from hospital.config.timeformat import format_for_web_second, format_forweb_no_HMS
from hospital.control.CDoctor import CDoctor
from hospital.extensions.interface.user_interface import doctor_required, is_doctor, token_required, is_user
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, StatusError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.extensions.tasks import add_async_task, change_consultation_status, cancel_async_task
from hospital.models import Departments, Doctor, Consultation, User, Enroll
from hospital.config.enums import ConsultationStatus


class CConsultation(CDoctor):
    def __init__(self):
        pass

    @token_required
    def list(self):
        data = parameter_required()
        constatus = data.get('constatus', 0)
        doid = data.get('doid')
        condate = data.get('condate')

        filter_args = [Consultation.isdelete == 0, ]
        if is_doctor():
            doid = getattr(request, 'user').id

        if doid:
            filter_args.append(Consultation.DOid == doid)
        if not constatus and is_user():
            filter_args.append(Consultation.CONstatus == ConsultationStatus.ready.value)
        elif constatus:
            try:
                constatus = ConsultationStatus(int(str(constatus))).value
            except:
                raise ParamsError('状态筛选参数异常')
            filter_args.append(Consultation.CONstatus == constatus)

        if condate:
            if not isinstance(condate, date):
                try:
                    condate = datetime.strptime(str(condate), format_forweb_no_HMS).date()
                except:
                    raise ParamsError('日期筛选 {} 参数错误'.format(data.get('condate')))
            filter_args.append(cast(Consultation.CONstartTime, Date) == condate)

        con_list = Consultation.query.filter(
            *filter_args).order_by(Consultation.createtime.desc()).all_with_page()

        for con in con_list:
            self._fill_doctor_mainpic(con)
            con_count = db.session.query(func.count(Enroll.ENid)).filter(
                Enroll.CONid == con.CONid, Enroll.isdelete == 0).scalar()
            con.fill('conremainder', (int(con.CONlimit) - int(con_count)))
        return Success('获取成功', data=con_list)

    @doctor_required
    def add_or_update_consultation(self):
        data = parameter_required()
        doid = getattr(request, 'user').id
        conid = data.get('conid')
        constarttime, conendtime, conlimit, constatus = data.get('constarttime'), data.get('conendtime'), \
                                                        data.get('conlimit'), data.get('constatus')

        constarttime = self._check_time(constarttime)
        conendtime = self._check_time(conendtime)
        now = datetime.now()
        if constarttime and constarttime < now:
            raise ParamsError('开始时间不能小于当前时间')
        if constarttime and conendtime and constarttime > conendtime:
            raise ParamsError('结束时间不能小于开始时间')

        if conlimit:
            try:
                conlimit = int(str(conlimit))
                if conlimit < 0:
                    raise ParamsError('限制人数只能为正整数')
            except:
                raise ParamsError('限制人数只能为正整数')

        if constatus:
            try:
                constatus = ConsultationStatus(int(str(constatus))).value
            except:
                raise ParamsError('状态修改参数异常')

        with db.auto_commit():
            if conid:
                con = Consultation.query.filter(
                    Consultation.CONid == conid, Consultation.isdelete == 0).first()
                current_app.logger.info('get doctor {} '.format(con))
                # 优先判断删除
                if data.get('delete'):
                    if not con:
                        raise ParamsError('医生已删除')
                    current_app.logger.info('删除会诊 {}'.format(conid))
                    con.isdelete = 1
                    db.session.add(con)
                    cancel_async_task(conn_id='change_consultation{}'.format(conid))  # 取消已有定时任务
                    return Success('删除成功', data=conid)

                # 执行update
                if con:
                    cancel_async_task(conn_id='change_consultation{}'.format(conid))  # 取消已有定时任务
                    #  只能修改这个4个字段
                    update_dict = {}
                    if constarttime:
                        update_dict['CONstartTime'] = constarttime
                    if conendtime:
                        update_dict['CONendTime'] = conendtime
                    if constatus:
                        update_dict['CONstatus'] = constatus
                    if conlimit:
                        update_dict['CONlimit'] = conlimit
                    con.update(update_dict)
                    current_app.logger.info('更新会诊信息 {}'.format(conid))
                    db.session.add(con)
                    # 到开始时间更改状态, 除手动关闭外
                    if constatus != ConsultationStatus.finish.value:
                        add_async_task(func=change_consultation_status, start_time=constarttime,
                                       func_args=(conid,), conn_id='change_consultation{}'.format(conid))
                    return Success('更新成功', data=conid)
            # 添加
            data = parameter_required({
                'constarttime': '开始时间', 'conlimit': '限制人数'
            })

            conid = str(uuid.uuid1())
            doctor = Doctor.query.filter(Doctor.DOid == doid, Doctor.isdelete == 0).first_('医生已删除')
            dep = Departments.query.filter(Departments.DEid == doctor.DEid, Departments.isdelete == 0).first_('科室已删除')
            con = Consultation.create({
                'CONid': conid,
                'DOid': doid,
                'CONstartTime': constarttime,
                'CONendTime': conendtime,
                'CONlimit': conlimit,
                'CONnote': data.get('connote'),
                'DOname': doctor.DOname,
                'DOtel': doctor.DOtel,
                'DOtitle': doctor.DOtitle,
                'DOdetails': doctor.DOdetails,
                'DOwxid': doctor.DOwxid,
                'DOskilledIn': doctor.DOskilledIn,
                'DEname': dep.DEname,
                'DEid': dep.DEid,
            })

            current_app.logger.info('创建会诊 {}'.format(doid))
            db.session.add(con)
            # 到开始时间更改状态
            add_async_task(func=change_consultation_status, start_time=constarttime,
                           func_args=(conid,), conn_id='change_consultation{}'.format(conid))
        return Success('创建会诊成功', data=conid)

    def _check_time(self, check_time):
        if not check_time:
            return
        # 日期校验
        if not isinstance(check_time, datetime):
            try:
                check_time = datetime.strptime(str(check_time), format_for_web_second)
            except:
                raise ParamsError('日期格式不对，具体格式为{}'.format(format_for_web_second))
        return check_time

    @token_required
    def add_enroll(self):
        data = parameter_required('conid')
        usid = getattr(request, 'user').id
        user = User.query.filter(User.USid == usid, User.isdelete == 0).first_('用户不存在')
        if not user.UStelphone:
            raise StatusError("请先在 '我的 - 我的家人' 中完善本人信息")
        conid = data.get('conid')
        con = Consultation.query.filter(Consultation.CONid == conid, Consultation.isdelete == 0).first_('会诊已结束')
        con_count = db.session.query(func.count(Enroll.ENid)).filter(
            Enroll.CONid == conid, Enroll.isdelete == 0).scalar()
        if con_count >= int(con.CONlimit):
            raise StatusError('名额已满')
        enroll_user = Enroll.query.filter(Enroll.USid == usid, Enroll.CONid == conid).first()
        if enroll_user:
            raise StatusError('已经报名成功')
        with db.auto_commit():
            enroll = Enroll.create({
                'ENid': str(uuid.uuid1()),
                'CONid': con.CONid,
                'USid': user.USid,
                'USname': user.USname,
                'UStelphone': user.UStelphone
            })
            db.session.add(enroll)
        return Success('报名成功')

    def list_enroll(self):
        data = parameter_required('conid')
        conid = data.get('conid')
        # conid 校验
        Consultation.query.filter(Consultation.CONid == conid, Consultation.isdelete == 0).first_("会诊不存在")
        enroll_list = Enroll.query.filter(Enroll.CONid == conid, Enroll.isdelete == 0).all_with_page()
        return Success('获取成功', data=enroll_list)
