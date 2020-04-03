# -*- coding: utf-8 -*-
from datetime import datetime

from flask import current_app
import uuid

from hospital.control.CDoctor import CDoctor
from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Departments,  Doctor, DoctorMedia, Consultation
from hospital.config.enums import DoctorMetiaType


class CConsultation(CDoctor):
    def __init__(self):
        pass

    def list(self):
        data = parameter_required()
        now = datetime.now()
        con_list = db.session.query.filter(
            Consultation.CONstatus == 1, Consultation.isdelete == 0, now <= Consultation.CONendTime,
            Doctor.isdelete == 0, Departments.isdelete == 0
        ).order_by(Consultation.createtime.desc()).all_with_page()

        for con in con_list:
            self._fill_doctor_mainpic(con)