# -*- coding: utf-8 -*-
from decimal import Decimal

from flask import current_app
import uuid

from sqlalchemy import or_, func
from werkzeug.security import generate_password_hash

from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, NotFound
from hospital.extensions.params_validates import parameter_required, validate_telephone
from hospital.extensions.register_ext import db
from hospital.models import Departments, Doctor, DoctorMedia, Consultation, Enroll, Review, Register
from hospital.config.enums import DoctorMetiaType, ConsultationStatus


class CDoctor(object):

    def get(self):
        data = parameter_required('doid')
        doid = data.get('doid')
        conid = data.get('conid')
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
        if conid:
            # 填充会诊信息
            self._fill_consultation(doctor, conid)

        # doctor.fill('favorablerate', '100%')
        # doctor.fill('treatnum', '0')
        self._fill_doctor_review(doctor)
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
            if doname:
                filter_args.append(Doctor.DOname.ilike('%{}%'.format(doname)))
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
            doctor.add('DOskilledIn')

            if index == 'doname':
                # todo 好评率 接诊次数
                # doctor.fill('favorablerate', '100%')
                # doctor.fill('treatnum', '0')
                self._fill_doctor_review(doctor)
            if index == 'back':
                doctor.add('DOtel')
                # todo 好评率 接诊次数
                # doctor.fill('favorablerate', '100%')
                # doctor.fill('treatnum', '0')
                self._fill_doctor_review(doctor)

        return Success('获取成功', data=doctors)

    @admin_required
    def add_or_update_doctor(self):
        data = parameter_required()
        doid = data.get('doid')
        # password = data.get('dopassword')
        dotel = data.get('dotel')
        if dotel:
            validate_telephone(dotel)
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
                    if Doctor.query.filter(Doctor.DOid != doid, Doctor.DOtel == dotel, Doctor.isdelete == 0).first():
                        raise ParamsError(f'已存在使用手机号"{dotel}"的其他医生账户, 请检查后重试')
                    update_dict = doctor.get_update_dict(data)
                    if update_dict.get('DOid'):
                        update_dict.pop('DOid')
                    if update_dict.get('DOsort', 0):
                        try:
                            int(update_dict.get('DOsort'))
                        except:
                            raise ParamsError('排序请输入整数')
                    if update_dict.get('DOpassword'):
                        update_dict.pop('DOpassword')

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

            if Doctor.query.filter(Doctor.DOtel == dotel, Doctor.isdelete == 0).first():
                raise ParamsError(f'已存在使用手机号"{dotel}"的医生账户, 请检查后重试')
            doid = str(uuid.uuid1())

            if data.get('dosort', 0):
                try:
                    int(data.get('dosort', 0))
                except:
                    raise ParamsError('排序请输入整数')

            doctor = Doctor.create({
                'DOid': doid,
                'DOname': data.get('doname'),
                'DOtel': dotel,
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
            current_app.logger.info('创建医生 {}'.format(data.get('doname')))
            db.session.add(doctor)
        return Success('创建医生成功', data=doid)

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
            doctor.fill('doctormainpic', dmmain['DMmedia'])
        else:
            doctor.fill('doctormainpic', '')

    def _fill_doctor_listpic(self, doctor):
        dmlist = DoctorMedia.query.filter(
            DoctorMedia.DOid == doctor.DOid,
            DoctorMedia.DMtype == DoctorMetiaType.listpic.value,
            DoctorMedia.isdelete == 0).order_by(
            DoctorMedia.DMsort.desc(), DoctorMedia.createtime.desc()).all()
        dm_fill_list = [dm['DMmedia'] for dm in dmlist]
        doctor.fill('doctorlistpic', dm_fill_list)

    def _fill_doctor_qrpic(self, doctor):
        dmqrpic = DoctorMedia.query.filter(
            DoctorMedia.DOid == doctor.DOid,
            DoctorMedia.DMtype == DoctorMetiaType.qrpic.value,
            DoctorMedia.isdelete == 0).first()
        if dmqrpic:
            doctor.fill('doctorqrpic', dmqrpic['DMmedia'])
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
        DoctorMedia.query.filter(DoctorMedia.DMid.notin_(dmid_list), DoctorMedia.DOid == doctor.DOid,
                                 DoctorMedia.isdelete == 0).delete_(synchronize_session=False)

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

    def _fill_consultation(self, doctor, conid):
        con = Consultation.query.filter(Consultation.CONid == conid, Consultation.DOid == doctor.DOid,
                                        Consultation.isdelete == 0).first()
        if con:
            self._fill_doctor_qrpic(doctor)
            con_count = db.session.query(func.count(Enroll.ENid)).filter(
                Enroll.CONid == con.CONid, Enroll.isdelete == 0).scalar()
            doctor.fill('conremainder', (int(con.CONlimit) - int(con_count)))
            doctor.fill('DOname', con.DOname)
            doctor.fill('DOtel', con.DOtel)
            doctor.fill('DOtitle', con.DOtitle)
            doctor.fill('DOdetails', con.DOdetails)
            doctor.fill('DOwxid', con.DOwxid)
            doctor.fill('DOskilledIn', con.DOskilledIn)
            doctor.fill('dename', con.DEname)
            doctor.fill('CONstartTime', con.CONstartTime)
            doctor.fill('CONid', con.CONid)
            doctor.fill('CONlimit', con.CONlimit)
            doctor.fill('CONstatus', con.CONstatus)
            doctor.fill('CONstatus_zh', ConsultationStatus(con.CONstatus).zh_value)
            doctor.fill("CONnote", con.CONnote)

    def _fill_doctor_review(self, doctor):
        doid = doctor.DOid
        review_good = Review.query.filter(Review.isdelete == 0, Review.RVnum >= 4, Review.DOid == doid).all()
        review = Review.query.filter(Review.isdelete == 0, Review.DOid == doid).all()

        current_app.logger.info('get review good = {} review = {}'.format(len(review_good), len(review)))
        if len(review) == 0:
            # 无评论情况下默认100%好评率
            review_percentage = Decimal('1')
        else:
            review_percentage = Decimal(str(len(review_good) / len(review) or 0))
        doctor.fill("favorablerate", "{0}%".format((review_percentage * 100).quantize(Decimal('0.0'))))  # 好评率
        register = Register.query.filter(Register.DOid == doid, Register.isdelete == 0).all()
        doctor.fill("treatnum", len(register))  # 接诊次数