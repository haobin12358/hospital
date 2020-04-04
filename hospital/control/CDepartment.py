# -*- coding: utf-8 -*-
from flask import current_app
import uuid

from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Departments, Symptom, Doctor, DoctorMedia
from hospital.config.enums import DoctorMetiaType


class CDepartment(object):

    def __init__(self):
        pass

    def _fill_dep_details(self, dep, index=None):
        dep.fields = '__all__'
        symptoms = Symptom.query.filter(Symptom.DEid == dep.DEid, Symptom.isdelete == 0).order_by(
            Symptom.SYsort.asc(), Symptom.createtime.asc()).all()
        # 症状填充
        dep.fill('symptoms', symptoms)
        if index:
            return
        # 医生列表填充
        dos = Doctor.query.filter(Doctor.DEid == dep.DEid, Doctor.isdelete == 0).order_by(
            Doctor.DOsort.asc(), Doctor.createtime.desc()).all()
        for do in dos:
            do.add('DOskilledIn')
            do.fill('dename', dep.DEname)
            # 医生主图
            dmmain = DoctorMedia.query.filter(
                DoctorMedia.DOid == do.DOid,
                DoctorMedia.DMtype == DoctorMetiaType.mainpic.value,
                DoctorMedia.isdelete == 0).first()
            if dmmain:
                do.fill('doctormainpic', dmmain.DMmedia)
            else:
                do.fill('doctormainpic', '')
        dep.fill('doctors', dos)

    def _add_or_update_symptom(self, dep, symptoms):
        if not isinstance(symptoms, list):
            return
        sysort = 1
        syid_list = []
        symptom_list = []
        for symptom_dict in symptoms:
            syname = symptom_dict.get('syname')
            # syid = symptom_dict.get('syid')
            symptom = Symptom.query.filter(
                Symptom.DEid == dep.DEid, Symptom.SYname == syname,
                Symptom.isdelete == 0).first()
            if symptom:
                symptom.SYsort = sysort
                # db.session.add(symptom)
                syid = symptom.SYid
            else:
                syid = str(uuid.uuid1())
                symptom = Symptom.create({
                    'SYid': syid,
                    'SYname': syname,
                    'SYsort': sysort,
                    'DEid': dep.DEid
                })
            syid_list.append(syid)
            symptom_list.append(symptom)
            sysort += 1
        db.session.add_all(symptom_list)

        # 删除多余
        Symptom.query.filter(Symptom.SYid.notin_(syid_list), Symptom.isdelete == 0).delete_(synchronize_session=False)

    def list(self):
        data = parameter_required('index')
        index = data.get('index')

        deps = Departments.query.filter(Departments.isdelete == 0).order_by(
            Departments.DEsort.asc(), Departments.createtime.desc()).all_with_page()
        for dep in deps:
            self._fill_dep_details(dep, index)
            if index == 'home':
                dep.add('DEicon')

            if index == 'appointment':
                dep.add('DEicon2')

        return Success(data=deps)

    def get(self):
        data = parameter_required('deid')
        deid = data.get('deid')
        # index = data.get('index')
        dep = Departments.query.filter(
            Departments.DEid == deid, Departments.isdelete == 0).first()
        # current_app.logger.info('get index {}'.format(index))
        self._fill_dep_details(dep)

        return Success(data=dep)

    @admin_required
    def add_or_update_dep(self):
        data = parameter_required()
        deid = data.get('deid', '')
        with db.auto_commit():
            if deid:
                dep = Departments.query.filter(
                    Departments.DEid == deid, Departments.isdelete == 0).first()
                # 优先判断删除
                if data.get('delete'):
                    if not dep:
                        raise ParamsError('科室已删除')
                    current_app.logger.info('删除科室 {}'.format(deid))
                    dep.isdelete = 1
                    db.session.add(dep)
                    return Success('删除成功', data=deid)

                # 执行update
                if dep:

                    update_dict = dep.get_update_dict(data)
                    if update_dict.get('DEid'):
                        update_dict.pop('DEid')
                    if update_dict.get('DEsort'):
                        try:
                            int(update_dict.get('DEsort'))
                        except:
                            raise ParamsError('排序请输入整数')
                    # 更新症状
                    if data.get('symptoms'):
                        self._add_or_update_symptom(dep, data.get('symptoms'))
                    dep.update(update_dict)
                    current_app.logger.info('更新科室 {}'.format(deid))
                    db.session.add(dep)
                    return Success('更新成功', data=deid)
            # 添加
            data = parameter_required(
                {'dename': '科室名', 'dalpha': '科室主图', 'deintroduction': '科室介绍',
                 'deicon': '科室小icon', 'deicon2': '科室大icon'})
            deid = str(uuid.uuid1())

            if data.get('desort', 0):
                try:
                    int(data.get('desort', 0))
                except:
                    raise ParamsError('排序请输入整数')

            dep = Departments.create({
                'DEid': deid,
                'DEname': data.get('dename'),
                'DEalpha': data.get('dalpha'),
                'DEintroduction': data.get('deintroduction'),
                'DEicon': data.get('deicon'),
                'DEsort': data.get('desort', 0),
                'DEicon2': data.get('deicon2')
            })
            if data.get('symptoms'):
                self._add_or_update_symptom(dep, data.get('symptoms'))
            current_app.logger.info('创建科室 {}'.format(data.get('dename')))
            db.session.add(dep)
        return Success('创建科室成功', data=deid)

    def list_sympotom(self):
        data = parameter_required('deid')
        deid = data.get('deid')
        sy_list = Symptom.query.filter(Symptom.DEid == deid, Symptom.isdelete == 0).order_by(
            Symptom.SYsort.asc(), Symptom.createtime.desc()).all_with_page()
        return Success('症状列表获取成功', data=sy_list)
