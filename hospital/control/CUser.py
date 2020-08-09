"""
本文件用于处理用户相关操作
create user: wiilz
last update time:2020/04/05 00:28
"""
import re
import os
import uuid
import random
import requests
from datetime import datetime
from sqlalchemy import false, true, or_, func
from flask import current_app, request
from id_validator import validator
from hospital.common.default_head import GithubAvatarGenerator
from hospital.common.identifying_code import SendSMS
from hospital.config.enums import FamilyRole, FamilyType, Gender, OrderPayType, WalletRecordType
from hospital.config.secret import MiniProgramAppId, MiniProgramAppSecret
from hospital.extensions.error_response import WXLoginError, ParamsError, NotFound, DumpliError, StatusError, \
    AuthorityError
from hospital.extensions.interface.user_interface import token_required, is_user, is_admin, admin_required
from hospital.extensions.params_validates import parameter_required, validate_chinese, validate_arg, validate_price
from hospital.extensions.register_ext import db, wx_pay
from hospital.extensions.request_handler import base_encode
from hospital.extensions.success_response import Success
from hospital.extensions.token_handler import usid_to_token
from hospital.extensions.weixin import WeixinLogin
from hospital.models import User, AddressProvince, AddressCity, AddressArea, UserAddress, Family, IdentifyingCode, \
    UserHour, OrderPay, WalletRecord


class CUser(object):

    def mini_program_login(self):
        """小程序登录"""
        data = parameter_required(('code', 'info'), )
        code = data.get("code")
        info = data.get("info")
        current_app.logger.info('info: {}'.format(info))
        userinfo = info.get('userInfo')
        if not userinfo:
            raise ParamsError('info 内参数缺失')

        session_key, openid, unionid = self.__parsing_code(code)
        if not unionid or not openid:
            unionid, openid = self.__parsing_encryped_data(unionid, openid, info, session_key)
        current_app.logger.info('get unionid is {}'.format(unionid))
        current_app.logger.info('get openid is {}'.format(openid))

        user = User.query.filter(User.isdelete == false(), User.USopenid == openid).first()
        head = self._get_local_head(userinfo.get("avatarUrl"), openid)
        sex = userinfo.get('gender', 0) if userinfo.get('gender') else Gender.woman.value

        with db.auto_commit():
            if user:
                current_app.logger.info('get exist user by openid: {}'.format(user.__dict__))
                user.update({'USavatar': head,
                             'USname': userinfo.get('nickName'),
                             'USgender': sex,
                             'USunionid': unionid,
                             })
            else:
                current_app.logger.info('This is a new guy : {}'.format(userinfo.get('nickName')))
                user_dict = {'USid': str(uuid.uuid1()),
                             'USname': userinfo.get('nickName'),
                             'USavatar': head,
                             'USgender': sex,
                             'USopenid': openid,
                             'USunionid': unionid,
                             }
                user = User.create(user_dict)
            db.session.add(user)

        token = usid_to_token(user.USid, level=user.USlevel, username=user.USname)
        data = {'token': token,
                'usname': user.USname,
                'usavatar': user['USavatar'],
                'uslevel': user.USlevel,
                'usbalance': 0,  # todo 对接会员卡账户
                }
        current_app.logger.info('return_data : {}'.format(data))
        return Success('登录成功', data=data)

    @staticmethod
    def __parsing_code(code):
        """解析code"""
        mplogin = WeixinLogin(MiniProgramAppId, MiniProgramAppSecret)
        try:
            get_data = mplogin.jscode2session(code)
            current_app.logger.info('get_code2session_response: {}'.format(get_data))
            session_key = get_data.get('session_key')
            openid = get_data.get('openid')
            unionid = get_data.get('unionid')
        except Exception as e:
            current_app.logger.error('mp_login_error : {}'.format(e))
            raise WXLoginError
        return session_key, openid, unionid

    def __parsing_encryped_data(self, unionid, openid, info, session_key):
        """解析加密的用户信息(unionid)"""
        current_app.logger.info('pre get unionid: {}'.format(unionid))
        current_app.logger.info('pre get openid: {}'.format(openid))
        encrypteddata = info.get('encryptedData')
        iv = info.get('iv')
        try:
            encrypted_user_info = self._decrypt_encrypted_user_data(encrypteddata, session_key, iv)
            unionid = encrypted_user_info.get('unionId')
            openid = encrypted_user_info.get('openId')
            current_app.logger.info('encrypted_user_info: {}'.format(encrypted_user_info))
        except Exception as e:
            current_app.logger.error('用户信息解密失败: {}'.format(e))
        return unionid, openid

    @staticmethod
    def _decrypt_encrypted_user_data(encrypteddata, session_key, iv):
        """小程序信息解密"""
        from ..common.WXBizDataCrypt import WXBizDataCrypt
        pc = WXBizDataCrypt(MiniProgramAppId, session_key)
        plain_text = pc.decrypt(encrypteddata, iv)
        return plain_text

    def _get_local_head(self, headurl, openid):
        """转置微信头像到服务器，用以后续二维码生成"""
        if not headurl:
            filedbname, filename = GithubAvatarGenerator().save_avatar(openid)
        else:
            data = requests.get(headurl)
            filename = openid + '.png'
            filepath, filedbpath = self._get_path('avatar')
            filedbname = os.path.join(filedbpath, filename)
            filename = os.path.join(filepath, filename)
            with open(filename, 'wb') as head:
                head.write(data.content)
        # 头像上传到阿里oss
        from hospital.control.CFile import CFile
        CFile().upload_to_oss(filename, filedbname[1:], '头像')
        return filedbname

    @staticmethod
    def _get_path(fold):
        """获取服务器上文件路径"""
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        filepath = os.path.join(current_app.config['BASEDIR'], 'img', fold, year, month, day)
        file_db_path = os.path.join('/img', fold, year, month, day)
        if not os.path.isdir(filepath):
            os.makedirs(filepath)
        return filepath, file_db_path

    def test_login(self):
        """测试登录"""
        data = parameter_required()
        tel = data.get('ustelphone')
        user = User.query.filter(User.isdelete == false(), User.UStelphone == tel).first()
        if not user:
            raise NotFound
        token = usid_to_token(user.USid, model='User', username=user.USname)
        return Success(data={'token': token, 'usname': user.USname})

    @staticmethod
    def get_provinces():
        """获取所有省份"""
        province_list = AddressProvince.query.filter(AddressProvince.isdelete == false()).all()
        return Success(data=province_list)

    @staticmethod
    def get_cities():
        """获取省份下的城市"""
        apid = parameter_required('apid').get('apid')
        city_list = AddressCity.query.filter(AddressCity.isdelete == false(), AddressCity.APid == apid).all()
        if not city_list:
            raise NotFound('未找到该省下的城市信息')
        return Success(data=city_list)

    @staticmethod
    def get_areas():
        """获取城市下的区县"""
        acid = parameter_required('acid').get('acid')
        area_list = AddressArea.query.filter(AddressArea.isdelete == false(), AddressArea.ACid == acid).all()
        if not area_list:
            raise NotFound('未找到该城市下的区县信息')
        return Success(data=area_list)

    @staticmethod
    def _combine_address_by_area_id(area_id):
        """拼接省市区"""
        try:
            address = db.session.query(AddressProvince.APname, AddressCity.ACname, AddressArea.AAname
                                       ).filter(AddressProvince.isdelete == false(),
                                                AddressCity.isdelete == false(),
                                                AddressArea.isdelete == false(),
                                                AddressCity.APid == AddressProvince.APid,
                                                AddressArea.ACid == AddressCity.ACid,
                                                AddressArea.AAid == area_id).first()
            address_str = ''.join(address)
        except Exception as e:
            current_app.logger.error('combine address str error : {}'.format(e))
            address_str = ''
        return address_str

    @staticmethod
    def _area_detail(area_id):
        """通过aaid返回三级地址详情"""
        apid, apname, acid, acname, aaname = db.session.query(AddressProvince.APid, AddressProvince.APname,
                                                              AddressCity.ACid, AddressCity.ACname, AddressArea.AAname
                                                              ).filter(AddressArea.AAid == area_id,
                                                                       AddressCity.ACid == AddressArea.ACid,
                                                                       AddressProvince.APid == AddressCity.APid,
                                                                       ).first()
        address_info = {'province': {'apid': apid, 'apname': apname},
                        'city': {'acid': acid, 'acname': acname},
                        'area': {'aaid': area_id, 'aaname': aaname}
                        }
        return address_info

    @token_required
    def set_address(self):
        """用户地址编辑"""
        data = request.json or {}
        uaid, uatel, aaid = data.get('uaid'), data.get('uatel'), data.get('aaid')
        uaname, uatext = data.get('uaname'), data.get('uatext')
        usid = getattr(request, 'user').id
        default_address = UserAddress.query.filter(UserAddress.isdelete == false(),
                                                   UserAddress.USid == usid,
                                                   UserAddress.UAdefault == true()
                                                   ).first()
        if aaid:
            AddressArea.query.filter(AddressArea.AAid == aaid).first_('参数错误：aaid')
        address_dict = {'USid': usid,
                        'UAname': str(uaname).replace(' ', '') if uaname else None,
                        'UAtel': str(uatel).replace(' ', '') if uatel else None,
                        'UAtext': str(uatext).replace(' ', '') if uatext else None,
                        'AAid': aaid}
        with db.auto_commit():
            if not uaid:  # 添加
                parameter_required({'uaname': "姓名", 'uatel': "手机号码",
                                    'uatext': "具体地址", 'aaid': "地址"}, datafrom=data)
                if not re.match(r'^1[1-9][0-9]{9}$', address_dict['UAtel']):
                    raise ParamsError('请填写正确的手机号码')
                address_dict['UAid'] = str(uuid.uuid1())
                address_dict['UAdefault'] = True if not default_address else False
                user_address = UserAddress.create(address_dict)
                msg = '添加成功'
            else:
                uadefault = bool(data.get('uadefault'))
                user_address = UserAddress.query.filter(UserAddress.isdelete == false(),
                                                        UserAddress.UAid == uaid,
                                                        UserAddress.USid == usid).first_('未找到该地址')
                if data.get('delete'):  # 删除
                    user_address.update({'isdelete': True})
                    msg = '删除成功'
                else:  # 更新
                    if uadefault and default_address and default_address.UAid != uaid:
                        UserAddress.query.filter(UserAddress.isdelete == false(), UserAddress.USid == usid,
                                                 UserAddress.UAid != user_address.UAid).update({'UAdefault': False})
                    if uatel and '*' not in uatel:
                        if not re.match(r'^1[1-9][0-9]{9}$', address_dict['UAtel']):
                            raise ParamsError('请填写正确的手机号码')
                    else:
                        del address_dict['UAtel']
                    address_dict['UAdefault'] = True if not uadefault and (not default_address or
                                                                           default_address.UAid == uaid
                                                                           ) else uadefault
                    user_address.update(address_dict)
                    msg = '更新成功'
            db.session.add(user_address)
        return Success(message=msg, data={'uaid': user_address.UAid})

    @token_required
    def address_list(self):
        usid = getattr(request, 'user').id
        address_list = UserAddress.query.filter(UserAddress.isdelete == false(),
                                                UserAddress.USid == usid
                                                ).order_by(UserAddress.UAdefault.desc(),
                                                           UserAddress.updatetime.desc()).all()
        for address in address_list:
            address.UAtel = str(address.UAtel)[:3] + '****' + str(address.UAtel)[7:]
            address.fill('address_str', f'{self._combine_address_by_area_id(address.AAid)} {address.UAtext}')
            address.hide('UAtext', 'USid')
        return Success(data=address_list)

    @token_required
    def address(self):
        """单地址详情"""
        args = parameter_required('uaid')
        usid = getattr(request, 'user').id
        address = UserAddress.query.filter(UserAddress.isdelete == false(),
                                           UserAddress.UAid == args.get('uaid'),
                                           UserAddress.USid == usid).first_('未找到该地址信息')
        address_info = self._area_detail(address.AAid)

        address.fill('address_info', address_info)
        address.hide('USid')
        return Success(data=address)

    @token_required
    def info(self):
        """用户详情"""
        if is_user():
            user = User.query.filter(User.isdelete == false(),
                                     User.USid == getattr(request, 'user').id).first_('未找到该用户信息')
            user.fields = ['USname', 'USavatar', 'USgender', 'USlevel', 'UStelphone', 'USintegral', 'USbalance']
            user.fill('usgender_zh', Gender(user.USgender).zh_value)
            # user.fill('usbalance', 0)  # todo 对接会员卡
            user.UStelphone = str(user.UStelphone)[:3] + '****' + str(user.UStelphone)[7:] if user.UStelphone else ''
        else:
            if not is_admin():
                raise AuthorityError
            args = parameter_required(('usid',))
            user = User.query.filter(User.isdelete == false(), User.USid == args.get('usid')).first_('未找到该用户信息')
            self._fill_user(user)
            # user.fill('usbalance', 0)  # todo 对接会员卡
        return Success(data=user)

    @token_required
    def recharge(self):
        """余额充值"""
        user = User.query.filter(User.isdelete == false(),
                                 User.USid == getattr(request, 'user').id).first_('未找到该用户信息')
        data = parameter_required(('cash_nums',))
        cash_nums = validate_price(data.get('cash_nums'), can_zero=False)
        from hospital.control.COrder import COrder
        with db.auto_commit():
            opayno = wx_pay.nonce_str
            body = f'wallet_recharge_{datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")}'
            op_instance = OrderPay.create({
                'OPayid': str(uuid.uuid1()),
                'OPayno': opayno,
                'OPayType': OrderPayType.wx.value,
                'OPayMount': cash_nums,
            })
            db.session.add(op_instance)
            pay_args = COrder()._pay_detail(opayno, cash_nums, body, openid=user.USopenid)
            pay_type = OrderPayType.wx.value

            wr = WalletRecord.create({
                'WRid': str(uuid.uuid1()),
                'USid': user.USid,
                'WRcash': cash_nums,
                'WRtype': WalletRecordType.recharge.value,
                'ContentId': op_instance.OPayid,
                'isdelete': True
            })
            db.session.add(wr)

            response = {
                'paytype': pay_type,
                'args': pay_args
            }
        return Success('成功', data=response)

    @staticmethod
    def _fill_user(user):
        user.fill('usgender_zh', Gender(user.USgender).zh_value)
        familys = Family.query.filter(Family.isdelete == false(),
                                      Family.USid == user.USid).order_by(Family.FAtype.asc()).all()
        for family in familys:
            family.hide('FArole', 'USid', 'FAself', 'AAid')
            family.fill('fagender_zh', Gender(family.FAgender).zh_value)
            family.fill('fatype_zh', FamilyType(family.FAtype).zh_value)
        user.fill('family', familys)

    @admin_required
    def list_user(self):
        args = parameter_required(('page_num', 'page_size'))
        uslevel = args.get('uslevel')
        us_query = User.query.filter(User.isdelete == false())
        if uslevel:
            validate_arg(r'^[0-4]$', str(uslevel), '参数错误: uslevel')
            us_query = us_query.filter(User.USlevel == uslevel)
        user_list = us_query.order_by(User.createtime.desc()).all_with_page()
        for user in user_list:
            user.fill('usgender_zh', Gender(user.USgender).zh_value)
            user.fill('usbalance', 0)  # todo 对接会员卡
            user.fill('uhnum', db.session.query(func.sum(UserHour.UHnum)
                                                ).filter(UserHour.isdelete == false(),
                                                         UserHour.USid == user.USid).scalar() or 0)
        return Success(data=user_list)

    @token_required
    def list_roles(self):
        usid = getattr(request, 'user').id
        data = [{'en': FamilyRole.myself.name, 'zh': FamilyRole.myself.zh_value, 'value': FamilyRole.myself.value,
                 'disable': bool(self._valid_exist_family_role([Family.USid == usid,
                                                                Family.FArole == FamilyRole.myself.value], ))},
                {'en': FamilyRole.spouse.name, 'zh': FamilyRole.spouse.zh_value, 'value': FamilyRole.spouse.value,
                 'disable': bool(self._valid_exist_family_role([Family.USid == usid,
                                                                Family.FArole == FamilyRole.spouse.value], ))},
                {'en': FamilyRole.child.name, 'zh': FamilyRole.child.zh_value, 'value': FamilyRole.child.value,
                 'disable': False}]
        return Success(data=data)

    @token_required
    def list_family(self):
        """家人列表"""
        family_list = Family.query.filter(Family.isdelete == false(),
                                          Family.USid == getattr(request, 'user').id
                                          ).order_by(Family.FAtype.asc()).all()
        for fa in family_list:
            fa.fill('fagender_zh', Gender(fa.FAgender).zh_value)
            fa.fill('fatype_zh', FamilyType(fa.FAtype).zh_value)
            fa.fill('farole_zh', FamilyRole(fa.FArole).zh_value)
            if fa.FAtel:
                fa.FAtel = str(fa.FAtel)[:3] + '****' + str(fa.FAtel)[7:]
            if fa.FAidentification:
                fa.FAidentification = str(fa.FAidentification)[:10] + '*' * 6 + str(fa.FAidentification)[16:]
        return Success(data=family_list)

    @token_required
    def family(self):
        """家人详情"""
        args = parameter_required('faid')
        family = self._valid_exist_family_role([Family.FAid == args.get('faid')], msg='未找到任何信息')
        family.fill('address_info', self._area_detail(family.AAid))
        family.fill('farole_zh', FamilyRole(family.FArole).zh_value)
        return Success(data=family)

    @token_required
    def set_family(self):
        """设置家人"""
        data = request.json or {}
        user = User.query.filter(User.isdelete == false(),
                                 User.USid == getattr(request, 'user').id).first_('用户信息有误')
        faname, fatel, faidentification, aaid, farole = map(lambda x: data.get(x),
                                                            ('faname', 'fatel', 'faidentification', 'aaid', 'farole'))
        faid = data.get('faid')
        required_dict = {'faname': '姓名', 'fatel': '手机号码', 'farole': '身份',
                         'faidentification': '身份证号', 'aaid': '居住地'
                         }
        if str(farole) == str(FamilyRole.child.value):
            del required_dict['fatel']
        parameter_required(required_dict, datafrom=data)
        if not validate_chinese(str(faname)):
            raise ParamsError('姓名中包含非汉语字符, 请检查姓名是否填写错误')
        if fatel and not re.match(r'^1[1-9][0-9]{9}$', str(fatel)):
            raise ParamsError('请填写正确的手机号码')
        if not re.match(r'^[1-3]$', str(farole)):
            raise ParamsError('参数错误：farole')
        id_valid = validator.get_info(faidentification)
        if not id_valid:
            raise ParamsError('请输入正确的身份证号码')
        age = self._calculate_age(id_valid.get('birthday_code'))
        # id_valid.get('sex') 1 为男性，0 为女性
        gender = Gender.man.value if str(id_valid.get('sex')) == str(Gender.man.value) else Gender.woman.value
        AddressArea.query.filter(AddressArea.AAid == aaid).first_('参数错误：aaid')

        fatype, faself = self._figure_out_family_role(str(farole), str(gender))

        family_dict = {'USid': user.USid,
                       'FArole': farole,
                       'FAtype': fatype,
                       'FAname': faname,
                       'FAage': age,
                       'FAidentification': faidentification,
                       'FAtel': fatel,
                       'FAgender': gender,
                       'AAid': aaid,
                       'FAaddress': self._combine_address_by_area_id(aaid),
                       'FAself': faself}
        with db.auto_commit():
            if not faid:
                if str(farole) == str(FamilyRole.myself.value) or str(farole) == str(FamilyRole.spouse.value):
                    if self._valid_exist_family_role([Family.USid == user.USid, Family.FArole == farole], ):
                        raise DumpliError('您已添加过 {} 角色'.format(FamilyRole(farole).zh_value))
                if self._valid_exist_family_role([Family.USid == user.USid,
                                                  or_(Family.FAidentification == faidentification,
                                                      Family.FAname == faname)], ):
                    raise DumpliError('您已添加过姓名为"{}"或身份证号码为"{}"的家人，'
                                      '请检查是否填写错误'.format(faname, faidentification))
                family_dict['FAid'] = str(uuid.uuid1())
                msg = '添加成功'
                family = Family.create(family_dict)
            else:
                family = self._valid_exist_family_role((Family.FAid == faid,), msg='未找到任何信息')
                if str(family.FArole) != str(farole) and self._valid_exist_family_role(
                        [Family.FAid != faid, Family.USid == user.USid, Family.FArole == farole], ):
                    raise ParamsError('您已创建过{},请到相应已有身份中修改信息'.format(FamilyRole(farole).zh_value))
                family.update(family_dict)
                msg = '更新成功'

            if faself:
                current_app.logger.info('添加家人为本人，更新user资料')
                user.update({'UStelphone': fatel, 'UScardid': faidentification, 'USgender': gender})
            db.session.add_all([family, user])

        return Success(message=msg, data={'faid': family.FAid})

    @staticmethod
    def _figure_out_family_role(farole, gender):
        faself = False
        if farole == str(FamilyRole.myself.value):
            faself = True
            res_type = FamilyType.father.value if gender == str(Gender.man.value) else FamilyType.mother.value
        elif farole == str(FamilyRole.spouse.value):
            res_type = FamilyType.father.value if gender == str(Gender.man.value) else FamilyType.mother.value
        else:
            res_type = FamilyType.son.value if gender == str(Gender.man.value) else FamilyType.daughter.value
        return res_type, faself

    @staticmethod
    def _valid_exist_family_role(filter_args, msg=None):
        return Family.query.filter(Family.isdelete == false(), *filter_args).first_(msg)

    @staticmethod
    def _calculate_age(birth_s):
        """计算年龄"""
        birth_d = datetime.strptime(birth_s, "%Y-%m-%d")
        today_d = datetime.now()
        birth_t = birth_d.replace(year=today_d.year)
        if today_d > birth_t:
            age = today_d.year - birth_d.year
        else:
            age = today_d.year - birth_d.year - 1
        return age

    @token_required
    def send_identifying_code(self):
        """发送验证码"""
        args = parameter_required('telphone')
        tel = args.get('telphone')
        if not tel or not re.match(r'^1[1-9][0-9]{9}$', str(tel)):
            raise ParamsError('请输入正确的手机号码')
        # 拼接验证码字符串（6位）
        code = ""
        while len(code) < 6:
            item = random.randint(1, 9)
            code = code + str(item)

        time_now = datetime.now()
        # 根据电话号码获取时间
        time_up = IdentifyingCode.query.filter(IdentifyingCode.isdelete == false(),
                                               IdentifyingCode.ICtelphone == tel
                                               ).order_by(IdentifyingCode.createtime.desc()).first()

        # 获取当前时间，与上一次获取的时间进行比较，小于60秒的获取进行提醒
        if time_up:
            delta = time_now - time_up.createtime
            current_app.logger.info("this is time up {}".format(delta))
            if delta.seconds < 60:
                raise StatusError("验证码已发送, 请稍后再试")
        with db.auto_commit():
            new_code = IdentifyingCode.create({
                "ICtelphone": tel,
                "ICcode": code,
                "ICid": str(uuid.uuid1())
            })
            db.session.add(new_code)

            try:
                response_send_message = SendSMS(tel, {"code": code})
                if not response_send_message:
                    raise NotImplementedError
            except Exception as e:
                current_app.logger.error('send identifying code error : {}'.format(e))
                raise StatusError('验证码获取失败')

        response = {'telphone': tel}
        return Success('获取验证码成功', data=response)

    @staticmethod
    def validate_identifying_code(telephone, identifying_code):
        """验证码校验"""
        if not telephone or not identifying_code:
            raise ParamsError("手机号/验证码缺失")
        res_code = IdentifyingCode.query.filter(IdentifyingCode.ICtelphone == telephone,
                                                IdentifyingCode.isdelete == false()
                                                ).order_by(IdentifyingCode.createtime.desc()).first()

        if not res_code or str(res_code.ICcode) != identifying_code:
            current_app.logger.info(
                'get identifying code:{}; res code:{}'.format(identifying_code, res_code.ICcode if res_code else None))
            raise ParamsError('验证码有误')

        time_now = datetime.now()
        if (time_now - res_code.createtime).seconds > 600:
            current_app.logger.info('time now = {}, send time = {}'.format(time_now, res_code.createtime))
            raise ParamsError('验证码已经过期')

    @token_required
    def get_secret_user_id(self):
        """获取base64编码后的usid"""
        usid = getattr(request, 'user').id
        secret_usid = base_encode(usid)
        return Success(data={'secret_usid': secret_usid})
