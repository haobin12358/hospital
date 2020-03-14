# -*- coding: utf-8 -*-
from flask import current_app
import uuid
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, NotFound
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Departments, Symptom, Doctor, DoctorMedia
from hospital.config.enums import DoctorMetiaType


class CDoctor():

    def get(self):
        data = parameter_required('doid')
        doid = data.get('doid')
        doctor = Doctor.query.filter(
            Doctor.DOid == doid, Doctor.isdelete == 0).first()
        if not doctor:
            raise ParamsError('医生已离开')

        doctor.fields = ['DEid', 'DOname', 'DOid', 'DOtitle',
                         'DOtel', 'DOdetails', 'DOwxid', 'DOskilledIn']
        self._fill_department(doctor)
        self._fill_doctor_mainpic(doctor)
        self._fill_doctor_listpic(doctor)
        self._fill_doctor_qrpic(doctor)
        return Success('获取成功', data=doctor)
        # todo 填充会诊信息 填充视频信息

    def list(self):
        data = parameter_required()
        deid = data.get('deid')  # 科室 姓名 科室职称 擅长 主图
        # onduty = data.get('onduty')
        # doname = data.get('doname') 姓名搜索 姓名 科室 职称 好评率 接诊次数 主图
        # todo 会诊安排筛选 姓名 科室 会诊开始时间 主图
        # todo 课程筛选
        # todo 专家团队筛选 姓名 职称 科室 主图
        # todo 后台列表 姓名 主图 电话 科室 职称 好评率 接诊次数
        filter_args = [
            Doctor.isdelete == 0
        ]
        if deid:
            filter_args.add(Doctor.DEid == deid)
        doctors = Doctor.query.filter(
            *filter_args).order_by(Doctor.DOsort.desc(), Doctor.createtime).all()
        return Success('获取成功', data=doctors)

    def _fill_department(self, doctor):
        dep = Departments.query.filter(
            Departments.DEid == doctor.DEid, Departments.isdelete == 0).first()
        if not dep:
            current_app.logger.info(
                '医生 {} 科室 {} 数据丢失'.format(doctor.DOname, doctor.DEid))
            raise NotFound('系统科室数据异常')
        doctor.fill('dename', dep.DEname)

    def _fill_doctor_mainpic(self, doctor):
        dmmain = DoctorMedia.query.filter(
            DoctorMedia.DOid == doctor.DOid,
            DoctorMedia.DMtype == DoctorMetiaType.mainpic.value,
            DoctorMedia.isdelete == 0).first()
        doctor.fill('doctormainpic', dmmain.DMmedia)

    def _fill_doctor_listpic(self, doctor):
        dmlist = DoctorMedia.query.filter(
            DoctorMedia.DOid == doctor.DOid,
            DoctorMedia.DMtype == DoctorMetiaType.listpic.value,
            DoctorMedia.isdelete == 0).order_by(
            DoctorMedia.DMsort.desc(), DoctorMedia.createtime.desc()).all()
        dm_fill_list = [dm.DMmedia for dm in dmlist]
        doctor.fill('doctorlistpic', dm_fill_list)

    def _fill_doctor_qrpic(self, doctor):
        dmqrpic = DoctorMedia.query.filter(
            DoctorMedia.DOid == doctor.DOid,
            DoctorMedia.DMtype == DoctorMetiaType.qrpic.value,
            DoctorMedia.isdelete == 0).first()
        doctor.fill('doctorqrpic', dmqrpic.DMmedia)
