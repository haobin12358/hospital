# -*- coding: utf-8 -*-
import re
from datetime import date, datetime

from flask import current_app, request
import uuid

from sqlalchemy import or_, and_

from hospital.config.enums import RegisterStatus
from hospital.config.timeformat import format_forweb_no_HMS
from .CUser import CUser
from hospital.extensions.interface.user_interface import token_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, NotFound
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Register, Family, Departments


class CRegister(CUser):
    def __init__(self):
        pass

    @token_required
    def list(self):
        data = parameter_required()
        usid = getattr(request, 'user').id
        telphone = data.get('telphone')
        restatus = data.get('restatus')
        # index = data.get('index')
        filter_args = [Register.isdelete == 0, Register.USid == usid, ]
        if telphone:
            family = Family.query.filter(Family.FAtel == telphone, Family.USid == usid,
                                         Family.isdelete == 0).first()
            if family:
                filter_args.append(Register.FAid == family.FAid)

        if restatus:
            filter_args.append(or_(Register.REstatus > RegisterStatus.transfer.value,
                                   Register.REstatus == RegisterStatus.cancle.value))

        else:
            filter_args.append(and_(Register.REstatus < RegisterStatus.commenting.value,
                                    Register.REstatus > RegisterStatus.cancle.value))
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
        if not isinstance(redate, date):
            try:
                redate = datetime.strptime(str(redate), format_forweb_no_HMS).date()

            except:
                return ParamsError('日期格式不对，具体格式为{}'.format(format_forweb_no_HMS))
        # 上午下午校验
        try:
            reamorpm = int(reamorpm)
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
            # todo 对接his
            db.session.add(register)
        return Success('预约成功{}，排队中'.format(dep.DEname))

    def _fill_resgister(self, register):
        restatus = register.REstatus
        register.fill('restatus_zh', RegisterStatus(restatus).zh_value)
        register.add('createtime')
        family = Family.query.filter(Family.FAid == register.FAid, Family.isdelete == 0).first()
        if family:
            register.fill('FAname', family.FAname)
            register.fill('FAtel', family.FAtel)
            register.fill('FAaddress', self._combine_address_by_area_id(family.AAid))
        dep = Departments.query.filter(Departments.DEid == register.DEid, Departments.isdelete == 0).first()
        if dep:
            register.fill('DEname', dep.DEname)

    @token_required
    def list_calling(self):
        usid = getattr(request, 'user').id
        # todo 对接his
        data = {"callinglist": [
            {
                "departmentname": "儿科",  # 科室名
                "currentnum": "78"  # 当前号
            },
            {
                "departmentname": "X放射科",  # 科室名
                "currentnum": "76"  # 当前号
            },
        ],
            "total": 3  # 共多少条记录
        }
        callinglist = []
        for calling in data.get('callinglist'):
            dep = Departments.query.filter(
                Departments.DEname == calling.get('departmentname'), Departments.isdelete == 0).first()
            if not dep:
                continue
            dep.fill('currentnum', calling.get('currentnum'))
            callinglist.append(dep)
        today = date.today()
        registerlist = Register.query.filter(Register.USid == usid, Register.isdelete == 0,
                                             Register.REdate == today).all()
        for register in registerlist:
            self._fill_resgister(register)
        return Success('获取叫号列表成功', data={
            'callinglist': callinglist,
            'registerlist': registerlist
        })
