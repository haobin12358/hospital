# -*- coding: utf-8 -*-
import re

from flask import current_app
import uuid

from sqlalchemy import or_
from werkzeug.security import generate_password_hash

from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, NotFound
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Departments, Symptom, Doctor, DoctorMedia
from hospital.config.enums import DoctorMetiaType


class CDoctor(object):

    def get(self):
        data = parameter_required('doid')
        doid = data.get('doid')
        doctor = Doctor.query.filter(
            Doctor.DOid == doid, Doctor.isdelete == 0).first()
        if not doctor:
            raise ParamsError('医生已离开')

        doctor.fields = ['DEid', 'DOname', 'DOid', 'DOtitle', 'DOtel', 'DOdetails',
                         'DOwxid', 'DOskilledIn', 'createtime', 'DOsort']
        self._fill_department(doctor)
        self._fill_doctor_mainpic(doctor)
        self._fill_doctor_listpic(doctor)
        self._fill_doctor_qrpic(doctor)
        doctor.fill('favorablerate', '100%')
        doctor.fill('treatnum', '0')
        return Success('获取成功', data=doctor)
        # todo 填充会诊信息 填充视频信息

    def list(self):
        data = parameter_required()
        deid = data.get('deid')  # 科室 姓名 科室职称 擅长 主图
        doname = data.get('doname')  # 姓名搜索 姓名 科室 职称 好评率 接诊次数 主图
        back = data.get('back')  # 后台列表 姓名 主图 电话 科室 职称 好评率 接诊次数
        filter_args = [Doctor.isdelete == 0, ]
        index = ''
        if deid:
            index = 'dep'
            filter_args.append(Doctor.DEid == deid)
        elif doname:
            index = 'doname'
            # todo doname 字段校验。
            filter_args.append(
                or_(Doctor.DOname.ilike('%{}%'.format(doname)), Doctor.DOtitle.ilike('%{}%'.format(doname))))
        elif back:
            index = 'back'
        doctors = Doctor.query.join(Departments, Departments.DEid == Doctor.DEid).filter(
            *filter_args).order_by(
            Departments.DEsort.asc(), Doctor.DOsort.asc(), Doctor.createtime.desc()).all_with_page()
        for doctor in doctors:
            self._fill_department(doctor)
            self._fill_doctor_mainpic(doctor)
            if index == 'dep':
                doctor.add('DOskilledIn')
            if index == 'doname':
                # todo 好评率 接诊次数
                doctor.fill('favorablerate', '100%')
                doctor.fill('treatnum', '0')
            if index == 'back':
                doctor.add('DOtel')
                # todo 好评率 接诊次数
                doctor.fill('favorablerate', '100%')
                doctor.fill('treatnum', '0')

        return Success('获取成功', data=doctors)

    @admin_required
    def add_or_update_doctor(self):
        data = parameter_required()
        doid = data.get('doid')
        password = data.get('dopassword')
        with db.auto_commit():
            if doid:
                doctor = Doctor.query.filter(
                    Doctor.DOid == doid, Doctor.isdelete == 0).first()
                current_app.logger.info('get doctor {} '.format(doctor))
                # 优先判断删除
                if data.get('delete'):
                    if not doctor:
                        raise ParamsError('医生已删除')
                    current_app.logger.info('删除科室 {}'.format(doid))
                    doctor.isdelete = 1
                    db.session.add(doctor)
                    return Success('删除成功', data=doid)

                # 执行update
                if doctor:
                    update_dict = doctor.get_update_dict(data)
                    if update_dict.get('DOid'):
                        update_dict.pop('DOid')
                    if update_dict.get('DOsort', 0):
                        try:
                            int(update_dict.get('DOsort'))
                        except:
                            raise ParamsError('排序请输入整数')
                    # if update_dict.get('DOpassword'):

                    if password and password != '*' * 6:
                        self.__check_password(password)
                        password = generate_password_hash(password)
                        update_dict['DOpassword'] = password
                    # 更新医生列表图片
                    if data.get('doctorlistpic'):
                        self._add_or_update_list_pic(doctor, data.get('doctorlistpic'))
                    # 更新医生主图
                    if data.get('doctormainpic'):
                        self._add_or_update_media_pic(doctor, data.get('doctormainpic'), DoctorMetiaType.mainpic.value)
                    # 更新医生二维码
                    if data.get('doctorqrpic'):
                        self._add_or_update_media_pic(doctor, data.get('doctorqrpic'), DoctorMetiaType.qrpic.value)

                    doctor.update(update_dict)
                    current_app.logger.info('更新医生 {}'.format(doid))
                    db.session.add(doctor)
                    return Success('更新成功', data=doid)
            # 添加
            data = parameter_required({
                'doname': '医生名', 'dotel': '医生电话', 'dotitle': '医生职称', 'deid': '科室',
                'doctormainpic': '医生主图', 'dodetails': '医生简介', 'dowxid': '医生微信ID',
                'doskilledin': '擅长方向'})

            doid = str(uuid.uuid1())

            if data.get('dosort', 0):
                try:
                    int(data.get('dosort', 0))
                except:
                    raise ParamsError('排序请输入整数')

            doctor = Doctor.create({
                'DOid': doid,
                'DOname': data.get('doname'),
                'DOtel': data.get('dotel'),
                'DOtitle': data.get('dotitle'),
                'DOdetails': data.get('dodetails'),
                'DOwxid': data.get('dowxid'),
                'DOskilledIn': data.get('doskilledin'),
                'DOsort': data.get('dosort', 0),
                'DOpassword': generate_password_hash(str(data.get('dotel'))[-6:]),
                'DEid': data.get('deid')
            })
            if data.get('doctorlistpic'):
                self._add_or_update_list_pic(doctor, data.get('doctorlistpic'))
            # 更新医生主图
            if data.get('doctormainpic'):
                self._add_or_update_media_pic(doctor, data.get('doctormainpic'), DoctorMetiaType.mainpic.value)
            # 更新医生二维码
            if data.get('doctorqrpic'):
                self._add_or_update_media_pic(doctor, data.get('doctorqrpic'), DoctorMetiaType.qrpic.value)
            current_app.logger.info('创建科室 {}'.format(data.get('dename')))
            db.session.add(doctor)
        return Success('创建科室成功', data=doid)

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
        if dmmain:
            doctor.fill('doctormainpic', dmmain.DMmedia)
        else:
            doctor.fill('doctormainpic', '')

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
        if dmqrpic:
            doctor.fill('doctorqrpic', dmqrpic.DMmedia)
        else:
            doctor.fill('doctorqrpic', '')

    def _add_or_update_list_pic(self, doctor, list_pic):
        if not isinstance(list_pic, list):
            return
        dmsort = 1
        dmid_list = []
        dm_list = []
        for pic in list_pic:
            if not isinstance(pic, str):
                continue
            media = DoctorMedia.query.filter(DoctorMedia.DOid == doctor.DOid, DoctorMedia.DMmedia == pic,
                                             DoctorMedia.DMtype == DoctorMetiaType.listpic.value).first()
            if media:
                media.DMsort = dmsort
                dmid = media.DMid
            else:
                dmid = str(uuid.uuid1())
                media = DoctorMedia.create({
                    'DMid': dmid,
                    'DOid': doctor.DOid,
                    'DMtype': DoctorMetiaType.listpic.value,
                    'DMsort': dmsort,
                    'DMmedia': pic
                })
            dmid_list.append(dmid)
            dm_list.append(media)
            dmsort += 1
        db.session.add_all(dm_list)

        # 删除多余
        DoctorMedia.query.filter(DoctorMedia.DMid.notin_(dmid_list), DoctorMedia.isdelete == 0).delete_(
            synchronize_session=False)

    def _add_or_update_media_pic(self, doctor, media_pic, dmtype=DoctorMetiaType.mainpic.value):
        if not isinstance(media_pic, str):
            return
        dmmain = DoctorMedia.query.filter(
            DoctorMedia.DOid == doctor.DOid,
            DoctorMedia.DMtype == dmtype,
            DoctorMedia.isdelete == 0).first()
        if dmmain:
            if dmmain.DMmedia != media_pic:
                dmmain.isdelete = 1
                db.session.add(dmmain)
            else:
                return
        dmmain_new = DoctorMedia.create({
            'DMid': str(uuid.uuid1()),
            'DOid': doctor.DOid,
            'DMtype': dmtype,
            'DMmedia': media_pic,
            'DMsort': 0
        })

        db.session.add(dmmain_new)

    def __check_password(self, password):
        if not password or len(password) < 4:
            raise ParamsError('密码长度低于4位')
        zh_pattern = re.compile(r'[\u4e00-\u9fa5]+')
        match = zh_pattern.search(password)
        if match:
            raise ParamsError(u'密码包含中文字符')
        return True
