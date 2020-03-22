# -*- coding: utf-8 -*-
import re
from datetime import datetime

from flask import current_app
import uuid

from sqlalchemy import or_

from hospital.config.enums import Gender
from hospital.extensions.interface.user_interface import admin_required, is_admin
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, NotFound, AuthorityError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.models import Departments, Symptom, Example


class CExample(object):

    def get(self):
        data = parameter_required('exid')
        exid = data.get('exid')
        exm = Example.query.filter(Example.EXid == exid, Example.isdelete == 0).first()
        if not exm:
            raise NotFound('案例已删除')

        self._fill_example(exm, 'details')
        return Success('获取成功', data=exm)

    def list(self):
        data = parameter_required()
        syid = data.get('syid')
        examples_sql = Example.query.filter(Example.isdelete == 0)
        if syid:
            examples_sql.filter(Example.SYid == syid)
        else:
            if not is_admin():
                raise AuthorityError()
        examples = examples_sql.order_by(Example.EXsort.asc(), Example.createtime.desc()).all_with_page()
        for exm in examples:
            self._fill_example(exm)

        return Success('获取成功', data=examples)

    def add_or_update_example(self):
        data = parameter_required()
        exid = data.get('exid')
        with db.auto_commit():
            if exid:
                exm = Example.query.filter(
                    Example.EXid == exid, Example.isdelete == 0).first()
                # 优先判断删除
                if data.get('delete'):
                    if not exm:
                        raise ParamsError('案例已删除')
                    current_app.logger.info('删除科室 {}'.format(exid))
                    exm.isdelete = 1
                    db.session.add(exm)
                    return Success('删除成功', data=exid)

                # 执行update
                if exm:
                    update_dict = self._get_update_dict(exm, data)
                    if update_dict.get('EXid'):
                        update_dict.pop('EXid')
                    if update_dict.get('EXtreated'):
                        extreated = update_dict.get('EXtreated')
                        if not isinstance(extreated, datetime):
                            self._trans_time(str(extreated))
                    if update_dict.get('EXsort'):
                        try:
                            int(update_dict.get('EXsort'))
                        except:
                            raise ParamsError('排序请输入整数')
                    if update_dict.get('EXgender'):
                        try:
                            update_dict['EXgender'] = Gender(update_dict.get('EXgender')).value
                        except:
                            raise ParamsError('性别数据有误')
                    exm.update(update_dict)
                    current_app.logger.info('更新科室 {}'.format(exid))
                    db.session.add(exm)
                    return Success('更新成功', data=exid)
            # 添加
            data = parameter_required(
                {'exname': '患者姓名', 'exgender': '性别', 'exage': '年龄', 'syid': '症状',
                 'exheight': '身高', 'exweight': '体重', 'exalpha': '主图'})
            exid = str(uuid.uuid1())

            if data.get('exsort', 0):
                try:
                    int(data.get('exsort', 0))
                except:
                    raise ParamsError('排序请输入整数')

            exm = Example.create({
                'EXid': exid,
                "SYid": data.get('syid'),
                'EXname': data.get('exname'),
                'EXgender': data.get('exgender'),
                'EXage': data.get('exage'),
                'EXheight': data.get('exheight'),
                'EXweight': data.get('exweight'),
                'EXaddr': data.get('exaddr'),
                'EXtreated': data.get('extreated'),
                'EXchiefComplaint': data.get('exchiefcomplaint'),
                'EXclinicVisitHistory': data.get('exclinicvisithistory'),
                'EXcaseAnalysis': data.get('excaseanalysis'),
                'EXinspectionResults': data.get('exinspectionresults'),
                'EXdiagnosis': data.get('exdiagnosis'),
                'EXtreatmentPrinciple': data.get('extreatmentprinciple'),
                'EXtreatmentOutcome': data.get('extreatmentoutcome'),
                'EXperoration': data.get('experoration'),
                'EXbriefIntroduction': data.get('exbriefintroduction'),
                'EXalpha': data.get('exalpha'),
                'EXsort': data.get('exsort'),
            })

            current_app.logger.info('创建案例 {}'.format(data.get('exname')))
            db.session.add(exm)
        return Success('创建科室成功', data=exid)

    def _fill_example(self, exm, index='list'):
        if index == 'list':
            exm.add('EXbriefIntroduction')
        elif index == 'back':
            exm.add('EXname')
            self._fill_symptom(exm)
        else:
            exm.fields = '__all__'
            exm.fill('exgender_zh', Gender(exm.EXgender).zh_value)
            self._fill_symptom(exm)

    def _fill_symptom(self, exm):
        symptom = Symptom.query.filter(Symptom.SYid == exm.SYid, Symptom.isdelete == 0).first()
        if not symptom:
            current_app.logger.info('该案例关联到的症状已删除 EXid {}'.format(exm.EXid))
            exm.fill('syname', '')
            exm.fill('deid', '')
            exm.fill('dename', '')
        else:
            exm.fill('syname', symptom.SYname)
            exm.fill('deid', symptom.DEid)
            dep = Departments.query.filter(Departments.DEid == symptom.DEid, Departments.isdelete == 0).first()
            if dep:
                exm.fill('dename', dep.DEname)
            else:
                current_app.logger.info('该症状关联到的科室已删除 SYid {}'.format(symptom.SYid))
                exm.fill('dename', '')

    def _get_update_dict(self, instance_model, data_model):
        update_dict = dict()
        for key in instance_model.keys():
            lower_key = str(key).lower()
            if data_model.get(lower_key) or data_model.get(lower_key) == 0:
                update_dict.setdefault(key, data_model.get(lower_key))
        return update_dict

    def _trans_time(self, time_str):
        return_str = None
        try:
            if re.match(r'^\d{4}(-\d{2}){2} \d{2}(:\d{2}){2}$', time_str):
                return_str = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            elif re.match(r'^\d{4}(-\d{2}){2} \d{2}:\d{2}$', time_str):
                return_str = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        except ValueError:
            return_str = None
        if not return_str:
            raise ParamsError('请检查时间是否填写正确')
        return return_str
