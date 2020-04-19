"""
本文件用于处理公益援助申请，审核等操作
create user: wiilz
last update time:2020/3/26 18:17
"""
import uuid
import json
from sqlalchemy import false
from flask import current_app, request
from hospital.config.enums import FamilyType, ApplyStatus, AssistancePictureType, ApproveAction, Gender
from hospital.control.CUser import CUser
from hospital.extensions.error_response import ParamsError, DumpliError, AuthorityError
from hospital.extensions.interface.user_interface import token_required, is_user, admin_required, is_admin
from hospital.extensions.params_validates import parameter_required, validate_chinese, validate_arg, validate_datetime
from hospital.extensions.register_ext import db
from hospital.extensions.success_response import Success
from hospital.models import AssistanceRelatives, Assistance, AssistancePicture, User


class CAssistance(object):

    @token_required
    def apply(self):
        """申请"""
        data = parameter_required({'atname': '姓名', 'atbirthday': '出生年月', 'atgender': '性别',
                                   'athousehold': '户籍地址', 'ataddress': '家庭地址', 'attelphone': '手机号码',
                                   'idf_code': '验证码', 'arids': '申请人亲属', 'atcondition': '身体状况',
                                   'attreatment': '治疗情况', 'atdetail': '申请援助项目',
                                   'diagnosis': '诊断证明图片', 'poverty': '特困证明图片', 'atdate': '到院日期'})
        atname, atgender, atbirthday, attelphone, arids, atdate, diagnosis, poverty = map(lambda x: data.get(x), (
            'atname', 'atgender', 'atbirthday', 'attelphone', 'arids', 'atdate', 'diagnosis', 'poverty'))
        if not validate_chinese(atname):
            raise ParamsError('姓名中包含非汉语字符, 请检查姓名是否填写错误')
        validate_arg(r'^[1-2]$', atgender, '参数错误: atgender')
        validate_arg(r'^1[1-9][0-9]{9}$', attelphone, '请输入正确的手机号码')
        [self._exist_assistance_relative([AssistanceRelatives.ARid == arid], 'arid不存在') for arid in arids]
        if not validate_datetime(atbirthday):
            raise ParamsError('参数错误: atbirthday')
        if not validate_datetime(atdate):
            raise ParamsError('参数错误: ardate')
        CUser().validate_identifying_code(attelphone, data.get('idf_code'))
        assistance_dict = {'ATid': str(uuid.uuid1()), 'USid': getattr(request, 'user').id,
                           'ATname': atname, 'ATbirthday': atbirthday, 'ATgender': atgender,
                           'AThousehold': data.get('athousehold'), 'ATaddress': data.get('ataddress'),
                           'ATtelphone': attelphone, 'ARids': json.dumps(arids),
                           'ATcondition': data.get('atcondition'), 'ATtreatment': data.get('attreatment'),
                           'AThospital': data.get('athospital'), 'ATdetail': data.get('atdetail'),
                           'ATdate': atdate, 'ATincomeProof': data.get('atincomeproof'),
                           'ATstatus': ApplyStatus.waiting.value
                           }
        if self._exist_assistance([Assistance.USid == assistance_dict['USid'],
                                   Assistance.ATstatus == ApplyStatus.waiting.value]):
            raise DumpliError('您已有申请在审核中，等待审核结果后，可再次提交')

        instance_list = []
        with db.auto_commit():
            assistance = Assistance.create(assistance_dict)
            instance_list.append(assistance)
            [instance_list.append(AssistancePicture.create({'APid': str(uuid.uuid1()),
                                                            'ATid': assistance_dict['ATid'],
                                                            'APtype': AssistancePictureType.diagnosis.value,
                                                            'APimg': img_url})) for img_url in diagnosis]
            [instance_list.append(AssistancePicture.create({'APid': str(uuid.uuid1()),
                                                            'ATid': assistance_dict['ATid'],
                                                            'APtype': AssistancePictureType.poverty.value,
                                                            'APimg': img_url})) for img_url in poverty]

            db.session.add_all(instance_list)
        return Success('提交成功', data={'ATid': assistance_dict['ATid']})

    @token_required
    def get_assistance(self):
        if is_user():
            usid = getattr(request, 'user').id
            assistance = Assistance.query.filter(Assistance.isdelete == false(), Assistance.USid == usid
                                                 ).order_by(Assistance.createtime.desc()).first()
            res = {}
            if assistance:
                current_app.logger.info(f'get assistance id: {assistance.ATid}')
                res['atstatus'] = assistance.ATstatus
                res['atstatus_zh'] = ApplyStatus(assistance.ATstatus).zh_value
                res['can_submit'] = False if assistance.ATstatus == ApplyStatus.waiting.value else True
            return Success(data=res)
        else:
            if not is_admin():
                raise AuthorityError
            args = parameter_required('atid')
            assistance = Assistance.query.filter(Assistance.isdelete == false(),
                                                 Assistance.ATid == args.get('atid')).first_('未找到申请信息')
            self._fill_assistance(assistance)

            # 添加证明图片
            dia_pics, pove_pics = [], []
            as_pics = AssistancePicture.query.filter(AssistancePicture.isdelete == false(),
                                                     AssistancePicture.ATid == assistance.ATid
                                                     ).order_by(AssistancePicture.createtime.asc()).all()
            [dia_pics.append(pic) if pic.APtype == AssistancePictureType.diagnosis.value else pove_pics.append(pic) for
             pic in as_pics]
            assistance.fill('diagnosis', dia_pics)
            assistance.fill('poverty', pove_pics)
            # 添加亲属信息
            relatives_list = []
            for arid in json.loads(assistance.ARids):
                relative = self._exist_assistance_relative([AssistanceRelatives.ARid == arid, ])
                if not relative:
                    current_app.logger.error('arid not found: {}'.format(arid))
                    continue
                relative.fill('artype_zh', FamilyType(relative.ARtype).zh_value)
                relatives_list.append(relative)
            assistance.fill('relatives', relatives_list)
            return Success(data=assistance)

    @staticmethod
    def _fill_assistance(assistance):
        assistance.fill('atstatus_zh', ApplyStatus(assistance.ATstatus).zh_value)  # 审核状态
        assistance.fill('atgender_zh', Gender(assistance.ATgender).zh_value)  # 性别
        apply_user = User.query.filter(User.isdelete == false(), User.USid == assistance.USid).first()
        # 添加申请人账号信息
        assistance.fill('user_info', {'usname': apply_user.USname,
                                      'usavatar': apply_user['USavatar']} if apply_user else None)

    @admin_required
    def list_assistance(self):
        """管理员获取申请列表"""
        args = parameter_required(('page_num', 'page_size'))
        as_query = Assistance.query.filter(Assistance.isdelete == false())
        atstatus = args.get('atstatus')
        if atstatus:
            try:
                atstatus = int(atstatus)
                ApplyStatus(atstatus)
            except ValueError:
                raise ParamsError('atstatus 参数错误')
            as_query = as_query.filter(Assistance.ATstatus == atstatus)
        if args.get('usid'):
            as_query = as_query.filter(Assistance.USid == args.get('usid'))
        assistance_list = as_query.order_by(Assistance.createtime.desc()).all_with_page()
        [self._fill_assistance(assistance) for assistance in assistance_list]
        return Success(data=assistance_list)

    @admin_required
    def approve(self):
        """管理员审批"""
        data = request.json
        atids = data.get('atids')
        if not isinstance(atids, list):
            raise ParamsError('atids 格式错误， 应为["id1","id2"]')
        if not all(atids):
            raise ParamsError('null type in atids')

        action = data.get('action')
        try:
            action = int(action)
            ApproveAction(action)
        except ValueError:
            raise ParamsError('参数错误：action')
        atstatus = ApplyStatus.passed.value if ApproveAction.agree.value == action else ApplyStatus.reject.value
        instance_list = []
        with db.auto_commit():
            for atid in atids:
                assistance = self._exist_assistance([Assistance.ATid == atid, ])
                if not assistance:
                    current_app.logger.error('atid: {} not found'.format(atid))
                    continue
                assistance.update({'ATstatus': atstatus,
                                   'Reviewer': getattr(request, 'user').id, })
                instance_list.append(assistance)
            db.session.add_all(instance_list)
        return Success('成功')

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
        args = parameter_required('arid')
        arid = args.get('arid')
        usid = getattr(request, 'user').id
        relative = self._exist_assistance_relative([AssistanceRelatives.USid == usid,
                                                    AssistanceRelatives.ARid == arid], '未找到任何信息')
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

    @staticmethod
    def _exist_assistance(filter_args, msg=None):
        return Assistance.query.filter(Assistance.isdelete == false(), *filter_args).first_(msg)
