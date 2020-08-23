# -*- coding: utf-8 -*-
from datetime import date, datetime

from flask import current_app, request
import uuid
import random
from sqlalchemy import or_, and_

from hospital.config.enums import RegisterStatus, RegisterAmOrPm, DoctorMetiaType
from hospital.config.timeformat import format_forweb_no_HMS
from hospital.extensions.interface.user_interface import token_required, is_user, is_doctor, admin_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Register, Family, Departments, Doctor, DoctorMedia


class CRegister(object):
    def __init__(self):
        pass

    @token_required
    def list(self):
        data = parameter_required()
        restatus = int(data.get('restatus', 0))
        filter_args = [Register.isdelete == 0, ]
        if is_user():
            usid = getattr(request, 'user').id
            filter_args.append(Register.USid == usid)
            telphone = data.get('telphone')
            if restatus:
                filter_args.append(or_(Register.REstatus > RegisterStatus.transfer.value,
                                       Register.REstatus == RegisterStatus.cancle.value))
            else:
                filter_args.append(and_(Register.REstatus < RegisterStatus.commenting.value,
                                        Register.REstatus > RegisterStatus.cancle.value))
            if telphone:
                family = Family.query.filter(Family.FAtel == telphone, Family.USid == usid,
                                             Family.isdelete == 0).first()
                if family:
                    filter_args.append(Register.FAid == family.FAid)
        elif is_doctor():
            doctor = Doctor.query.filter(Doctor.DOid == getattr(
                request, 'user').id, Doctor.isdelete == 0).first_('账号已注销')
            filter_args.append(Register.DEid == doctor.DEid)
        # index = data.get('index')
        if not is_user():
            # 后台筛选专用字段
            if restatus:
                try:
                    restatus = RegisterStatus(int(str(restatus))).value
                except:
                    raise ParamsError('挂号状态筛选有误')
                filter_args.append(Register.REstatus == restatus)

            deid, usid, doid, redate, reamorpm = data.get('deid'), data.get('usid'), data.get(
                'doid'), data.get('redate'), data.get('reamorpm')
            if deid: filter_args.append(Register.DEid == deid)
            if usid: filter_args.append(Register.USid == usid)
            if doid: filter_args.append(Register.DOid == doid)
            redate = self._check_time(redate)
            if redate: filter_args.append(or_(Register.REdate == redate, Register.REtansferDate == redate))
            if reamorpm is not None:
                try:
                    reamorpm = RegisterAmOrPm(int(str(reamorpm))).value
                except:
                    raise ParamsError('时间段筛选有误')
                filter_args.append(or_(Register.REamOrPm == reamorpm, Register.REtansferAmOrPm == reamorpm))

        register_list = Register.query.filter(*filter_args).order_by(Register.createtime.desc()).all_with_page()
        for register in register_list:
            self._fill_resgister(register)
        return Success('获取成功', data=register_list)

    @token_required
    def add_register(self):
        data = parameter_required({'deid': '科室', 'redate': '日期', 'reamorpm': '上午或下午', 'faid': '就诊人'})
        usid = getattr(request, 'user').id
        deid, redate, faid, reamorpm = data.get('deid'), data.get('redate'), data.get('faid'), data.get('reamorpm')
        reremarks = data.get('reremarks')
        # 日期校验
        redate = self._check_time(redate)

        # 上午下午校验
        try:
            reamorpm = RegisterAmOrPm(int(str(reamorpm))).value
        except:
            reamorpm = 0
        # 就诊人信息校验
        family = Family.query.filter(
            Family.USid == usid, Family.FAid == faid, Family.isdelete == 0).first_('就诊人信息已删除')
        # 科室信息校验
        dep = Departments.query.filter(Departments.isdelete == 0, Departments.DEid == deid).first_('科室不存在')

        with db.auto_commit():
            register = Register.create({
                'REid': str(uuid.uuid1()),
                'DEid': deid,
                'USid': usid,
                'FAid': faid,
                'REdate': redate,
                'REamOrPm': reamorpm,
                'REremarks': reremarks
            })
            current_app.logger.info('创建挂号 科室 {} 就诊人 {}'.format(dep.DEname, family.FAname))

            db.session.add(register)
        return Success('预约成功{}，排队中'.format(dep.DEname))

    def _fill_resgister(self, register):
        if is_user():
            register.hide('USid')
        restatus = register.REstatus
        register.fill('restatus_zh', RegisterStatus(restatus).zh_value)
        if is_user():
            register.REcode = register.REcode or '等待排号中'
        reamorpm = register.REtansferAmOrPm
        if reamorpm is None:
            reamorpm = register.REamOrPm
        register.fill('reamorpm_zh', RegisterAmOrPm(reamorpm).zh_value)
        register.fill('reamorpm', reamorpm)
        register.fill('REdate', register.REtansferDate or register.REdate)

        register.add('createtime')
        family = Family.query.filter(Family.FAid == register.FAid, Family.isdelete == 0).first()
        if family:
            register.fill('FAname', family.FAname)
            register.fill('FAtel', family.FAtel)
            register.fill('FAaddress', family.FAaddress)
        dep = Departments.query.filter(Departments.DEid == register.DEid, Departments.isdelete == 0).first()
        if dep:
            register.fill('DEname', dep.DEname)

    @token_required
    def list_calling(self):
        usid = getattr(request, 'user').id
        # todo 对接his
        """
        data = {"callinglist": [
            {
                "departmentname": "未知",  # 科室名
                "currentnum": "0"  # 当前号
            }
        ],
            "total": 0  # 共多少条记录
        }
        callinglist = []
        for calling in data.get('callinglist'):
            dep = Departments.query.filter(
                Departments.DEname == calling.get('departmentname'), Departments.isdelete == 0).first()
            if not dep:
                continue
            dep.fill('currentnum', calling.get('currentnum'))
            callinglist.append(dep)
        """
        # todo call list fake data
        denames = db.session.query(Departments.DEname).filter(Departments.isdelete == 0
                                                              ).order_by(Departments.DEsort.asc(),
                                                                         Departments.createtime.desc(),
                                                                         origin=True).all()
        update_time = datetime.now().second % 60 or 1  # 每隔60秒更新一次
        callinglist = [{'dename': item[0], 'currentnum': '未知', 'update': f'{update_time}秒钟前'}
                       for item in denames if item]
        today = date.today()
        registerlist = Register.query.filter(Register.USid == usid, Register.isdelete == 0,
                                             Register.REdate == today).all()
        for register in registerlist:
            self._fill_resgister(register)
        return Success('获取叫号列表成功', data={
            'callinglist': callinglist,
            'registerlist': registerlist
        })

    def _check_time(self, check_time):
        if not check_time:
            return
        if not isinstance(check_time, date):
            try:
                check_time = datetime.strptime(str(check_time), format_forweb_no_HMS).date()

            except:
                return ParamsError('日期格式不对，具体格式为{}'.format(format_forweb_no_HMS))

        return check_time

    @admin_required
    def set_register(self):
        data = parameter_required('reid')
        with db.auto_commit():
            reid, recode, doid = data.get('reid'), data.get('recode'), data.get('doid')
            register = Register.query.filter(Register.REid == reid,
                                             Register.REstatus <= RegisterStatus.transfer.value,
                                             Register.isdelete == 0).first_('预约已操作完成')
            update_dict = {}
            # 优先判断是否填写预约号
            if recode:
                # 添加预约号
                retansferdate, retansferamorpm = data.get('retansferdate'), data.get('retansferamorpm')

                update_dict.setdefault('REcode', str(recode))
                retansferdate = self._check_time(retansferdate)
                try:
                    retansferamorpm = RegisterAmOrPm(int(str(retansferamorpm))).value
                except:
                    retansferamorpm = 0
                current_app.logger.info('get redate = {} and reamorpm = {}'.format(retansferdate, retansferamorpm))
                if retansferdate and retansferamorpm is not None:

                    update_dict.setdefault('REtansferDate', retansferdate)
                    update_dict.setdefault('REtansferAmOrPm', retansferamorpm)
                    update_dict.setdefault('REstatus', RegisterStatus.transfer.value)

                else:
                    update_dict.setdefault('REstatus', RegisterStatus.pending.value)

                register.update(update_dict)
                db.session.add(register)
                return Success('预约号填写成功')
            if not doid:
                return Success('未填写内容')
            doctor = Doctor.query.filter(Doctor.DOid == doid, Doctor.isdelete == 0).first_('医生不存在')
            dmmain = DoctorMedia.query.filter(
                DoctorMedia.DOid == doctor.DOid,
                DoctorMedia.DMtype == DoctorMetiaType.mainpic.value,
                DoctorMedia.isdelete == 0).first()
            if dmmain:
                update_dict.setdefault('DOmedia', dmmain['DMmedia'])

            update_dict.setdefault('DOid', doctor.DOid)
            update_dict.setdefault('DOtel', doctor.DOtel)
            update_dict.setdefault('DOtitle', doctor.DOtitle)
            update_dict.setdefault('DOname', doctor.DOname)
            update_dict.setdefault('REstatus', RegisterStatus.commenting.value)
            register.update(update_dict)
            db.session.add(register)
            return Success('设置主治医生成功')

    @admin_required
    def set_report(self):
        data = parameter_required(('reid', 'rereport'))
        reid, rereport = data.get('reid'), data.get('rereport')
        with db.auto_commit():
            register = Register.query.filter(Register.REid == reid, Register.isdelete == 0).first_('挂号记录已失效')
            register.update({'REreports': rereport, 'REstatus': 3})
            # register.REreports = rereport
            db.session.add(register)


        return Success('更新成功')

    # @token_required
    # def get_report(self):
    #     if is_user():
    #

