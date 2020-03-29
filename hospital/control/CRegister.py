# -*- coding: utf-8 -*-
import re
from datetime import date, datetime

from flask import current_app, request
import uuid

from sqlalchemy import or_, and_

from hospital.config.enums import RegisterStatus
from hospital.config.timeformat import format_forweb_no_HMS
from .CUser import CUser
from hospital.extensions.interface.user_interface import token_required, is_user
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, NotFound
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Series, Doctor, Register, User, Family, Departments


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
        Family.query.filter(
            Family.USid == usid, Family.FAid == faid, Family.isdelete == 0).first_('就诊人信息已删除')
        # 科室信息校验
        Departments.query.filter(Departments.isdelete == 0, Departments.DEid == deid).first_('科室不存在')

        with db.auto_commit:
            Register.create({
                'DEid': deid,
                'USid': usid,
                'FAid': faid,
                'REdate': redate,
                'REamOrPm': reamorpm,
                'REremarks': reremarks
            })
        return Success('预约成功，排队中')

    def _fill_resgister(self, register):
        restatus = register.REstatus
        register.fill('restatus_zh', RegisterStatus(restatus).zh_value)
        family = Family.query.filter(Family.FAid == register.FAid, Family.isdelete ==0).first()
        if family:
            register.fill('FAname', family.FAname)
            register.fill('FAtel', family.FAtel)
            register.fill('FAaddress', self._combine_address_by_area_id(family.AAid))



