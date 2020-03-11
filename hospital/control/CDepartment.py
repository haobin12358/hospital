# -*- coding: utf-8 -*-
from flask import current_app
import uuid
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Departments, Symptom, Doctor, DoctorMedia
from hospital.config.enums import DoctorMetiaType


class CDepartment(object):

    def __init__():
        pass

    def list(self):
        data = parameter_required('index')
        index = data.get('index')
        if index == 'home':
            pass
        deps = Departments.query.filter(Departments.isdelete == False()).order_by(
            Departments.DEsort.desc(), Departments.createtime.asc()).all()
        for dep in deps:
            if index == 'home'
                dep.fields.add('DEicon')
            if index == 'appointment':
                dep.fields.add('DEicon2')
            if index == 'back'
                self._fill_dep_details(dep)

        return Success(data=deps)

    def detais(self):
        data = parameter_required('deid', 'index')
        deid = data.get('deid')
        index = data.get('index')
        dep = Departments.query.filter(
            Departments.DEid == deid, Departments.isdelete == False).first()
        self._fill_dep_details(dep. index)
        return Success(data=dep)

    def _fill_dep_details(self, dep, index)
        dep.fields = '__all__'
        sys = Symptom.queyr.filter(Symptom.DEid == dep.DEid, Symptom.isdelete == False).order_by(
            Symptom.SYsort.desc(), Symptom.createtime.asc()).all()
        # 症状填充
        dep.fill('sys', sys)
        if index and str(index) == 'back':
            return
        # 医生列表填充
        dos = Doctor.query.filter(Doctor.DEid == dep.DEid, Doctor.isdelete == False).order_by(
            Doctor.DOsort.desc(), Doctor.createtime.asc()).all()
        for do in dos:
            do.fields.add('DOskilledIn')
            # 医生主图
            dmmain = DoctorMedia.query.filter(
                DoctorMedia.DOid == do.DOid,
                DoctorMedia.DMtype == DoctorMetiaType.mainpic.value,
                DoctorMedia.isdelete == False).first()
            do.fill('doctormainpic', dmmain.DMmedia)

    def add_or_update_dep()
        data = parameter_required()
        deid = data.get('deid', '')
        with db.auto_commit():
            if deid:
                dep = Departments.query.filter(
                    Departments.DEid == deid, Departments.isdelete == False).first()
                # 优先判断删除
                if data.get('delete'):
                    if not dep:
                        raise ParamsError('科室已删除')
                    current_app.logger.info('删除科室 {}'.format(deid))
                    dep.isdelete = True
                    db.session.add(dep)
                    return Success('删除成功', data=deid)

                # 执行update
                if dep:
                    # todo sort 整数校验
                    update_dict = self._get_update_dict(de, data)
                    if update_dict.get('DEid')
                        update_dict.pop('DEid')
                    dep.update(update_dict)
                    current_app.logger.info('更新科室 {}'.format(deid))
                    db.session.add(dep)
                    return Success('更新成功', data=deid)
            # 添加
            data = parameter_required(
                {'dename': '科室名', 'dalpha': '科室主图', 'deintroduction': '科室介绍',
                 'deicon': '科室小icon', 'deicon2': '科室大icon'})
            deid = str(uuid.uuid1())
            # todo sort 整数校验
            dep = Departments.create({
                'DEid': deid,
                'DEname': data.get('dename'),
                'DEalpha': data.get('dalpha'),
                'DEintroduction': data.get('deintroduction'),
                'DEicon': data.get('deicon'),
                'DEsort': data.get('desort'),
                'DEicon2': data.get('deicon2')
            })
            current_app.logger.info('创建科室 {}'.format(data.get('dename')))
            db.session.add(dep)
        return Success('创建科室成功', data=deid)

    def _get_update_dict(self, instance_model, data_model):
        update_dict = dict()
        for key in instance_model.keys():
            lower_key = str(key).lower()
            if data_model.get(lower_key) or data_model.get(lower_key) == 0:
                update_dict.setdefault(key, data_model.get(lower_key))
        return update_dict
