"""
本文件用于处理公益援助申请，审核等操作
create user: wiilz
last update time:2020/3/26 18:17
"""
import uuid
from sqlalchemy import false
from flask import current_app, request
from hospital.config.enums import FamilyType
from hospital.control.CUser import CUser
from hospital.extensions.error_response import ParamsError, DumpliError
from hospital.extensions.interface.user_interface import token_required
from hospital.extensions.params_validates import parameter_required, validate_chinese, validate_arg
from hospital.extensions.register_ext import db
from hospital.extensions.success_response import Success
from hospital.models import AssistanceRelatives


class CAssistance(object):

    def apply(self):
        """申请"""
        pass

    @token_required
    def relatives_type(self):
        usid = getattr(request, 'user').id
        data = [{'en': FamilyType.father.name, 'zh': FamilyType.father.zh_value, 'value': FamilyType.father.value,
                 'disable': bool(self._exist_assistance_relative([AssistanceRelatives.USid == usid,
                                                                  AssistanceRelatives.ARtype == FamilyType.father.value
                                                                  ], ))},
                {'en': FamilyType.mother.name, 'zh': FamilyType.mother.zh_value, 'value': FamilyType.mother.value,
                 'disable': bool(self._exist_assistance_relative([AssistanceRelatives.USid == usid,
                                                                  AssistanceRelatives.ARtype == FamilyType.mother.value
                                                                  ], ))}
                ]
        return Success(data=data)

    @token_required
    def list_relatives(self):
        """获取申请人亲属"""
        usid = getattr(request, 'user').id
        relatives = AssistanceRelatives.query.filter(AssistanceRelatives.isdelete == false(),
                                                     AssistanceRelatives.USid == usid
                                                     ).order_by(AssistanceRelatives.ARtype.asc(),
                                                                AssistanceRelatives.createtime.desc()).all()
        for re in relatives:
            re.fill('artype_zh', FamilyType(re.ARtype).zh_value)
        return Success(data=relatives)

    @token_required
    def relatives(self):
        """亲属详情"""
        usid = getattr(request, 'user').id
        relative = self._exist_assistance_relative([AssistanceRelatives.USid == usid, ], '未找到任何信息')
        relative.fill('artype_zh', FamilyType(relative.ARtype).zh_value)
        return Success(data=relative)

    @token_required
    def set_relatives(self):
        """添加/编辑亲属"""
        data = parameter_required({'artype': '身份', 'arname': '姓名', 'arage': '年龄',
                                   'arcompany': '工作单位', 'arsalary': '月收入'})
        usid = getattr(request, 'user').id
        arid, artype = data.get('arid'), data.get('artype')
        validate_arg(r'^[12]$', data.get('artype'), '参数错误: artype')
        arname, arage, arsalary = map(lambda x: str(data.get(x)).replace(' ', ''), ('arname', 'arage', 'arsalary'))
        if not validate_chinese(arname):
            raise ParamsError('姓名中包含非汉语字符, 请检查姓名是否填写错误')
        validate_arg(r'^[1-9](\d+)?$', arage, '请正确填写年龄')
        validate_arg(r'(^[1-9](\d+)?$)|(^0$)', arsalary, '请正确填写月收入')

        ar_dict = {'ARtype': artype,
                   'ARname': arname,
                   'ARage': arage,
                   'ARcompany': data.get('arcompany'),
                   'ARsalary': arsalary}
        with db.auto_commit():
            if not arid:
                if self._exist_assistance_relative([AssistanceRelatives.USid == usid,
                                                    AssistanceRelatives.ARname == arname,
                                                    AssistanceRelatives.ARtype == artype], ):
                    raise DumpliError('您已添加过 {}'.format(arname))
                ar_dict['ARid'] = str(uuid.uuid1())
                ar_dict['USid'] = usid
                ar = AssistanceRelatives.create(ar_dict)
                msg = '添加成功'
            else:
                ar = self._exist_assistance_relative([AssistanceRelatives.ARid == arid,
                                                      AssistanceRelatives.USid == usid], '未找到任何信息')
                if data.get('delete'):
                    ar.update({'isdelete': True})
                    msg = '删除成功'
                else:
                    if str(artype) != str(ar.ARtype) and self._exist_assistance_relative(
                            [AssistanceRelatives.USid == usid,
                             AssistanceRelatives.ARtype == artype,
                             AssistanceRelatives.ARid != ar.ARid], ):
                        raise ParamsError('您已添加过身份为 {} 的亲属，请到相应身份的亲属内修改'
                                          ''.format(FamilyType(artype).zh_value))
                    ar.update(ar_dict)
                    msg = '修改成功'
            db.session.add(ar)
        return Success(data={'arid': ar.ARid}, message=msg)

    @staticmethod
    def _exist_assistance_relative(filter_args, msg=None):
        return AssistanceRelatives.query.filter(AssistanceRelatives.isdelete == false(), *filter_args).first_(msg)
