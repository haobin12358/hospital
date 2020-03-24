"""
本文件用于处理用户相关操作
create user: wiilz
last update time:2020/3/24 01:28
"""
import re
import os
import uuid
import requests
from datetime import datetime
from sqlalchemy import false, true
from flask import current_app, request

from hospital.common.default_head import GithubAvatarGenerator
from hospital.config.secret import MiniProgramAppId, MiniProgramAppSecret
from hospital.extensions.error_response import WXLoginError, ParamsError, NotFound
from hospital.extensions.interface.user_interface import token_required
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.extensions.success_response import Success
from hospital.extensions.token_handler import usid_to_token
from hospital.extensions.weixin import WeixinLogin
from hospital.models import User, AddressProvince, AddressCity, AddressArea, UserAddress


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
        sex = userinfo.get('gender', 0)

        with db.auto_commit():
            if user:
                current_app.logger.info('get exist user by openid: {}'.format(user.__dict__))
                user.update({'USavatar': head,
                             'USname': userinfo.get('nickName'),
                             # 'USgender': sex,
                             'USunionid': unionid,
                             })
            else:
                current_app.logger.info('This is a new guy : {}'.format(userinfo.get('nickName')))
                user_dict = {'USid': str(uuid.uuid1()),
                             'USname': userinfo.get('nickName'),
                             'USavatar': head,
                             # 'USgender': sex,
                             'USopenid': openid,
                             'USunionid': unionid,
                             }
                user = User.create(user_dict)
            db.session.add(user)

        token = usid_to_token(user.USid, level=user.USlevel, username=user.USname)
        data = {'token': token,
                'usname': user.USname,
                'usavatar': user.USavatar,
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
            return GithubAvatarGenerator().save_avatar(openid)
        data = requests.get(headurl)
        filename = openid + '.png'
        filepath, filedbpath = self._get_path('avatar')
        filedbname = os.path.join(filedbpath, filename)
        filename = os.path.join(filepath, filename)
        with open(filename, 'wb') as head:
            head.write(data.content)
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
                parameter_required({'UAname': "姓名", 'UAtel': "手机号码",
                                    'UAtext': "具体地址", 'AAid': "地址"}, datafrom=address_dict)
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
                    if '*' not in uatel:
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
        apid, apname, acid, acname, aaname = db.session.query(AddressProvince.APid, AddressProvince.APname,
                                                              AddressCity.ACid, AddressCity.ACname, AddressArea.AAname
                                                              ).filter(AddressArea.AAid == address.AAid,
                                                                       AddressCity.ACid == AddressArea.ACid,
                                                                       AddressProvince.APid == AddressCity.APid,
                                                                       ).first()
        address_info = {'province': {'apid': apid, 'apname': apname},
                        'city': {'acid': acid, 'acname': acname},
                        'area': {'aaid': address.AAid, 'acname': aaname}
                        }

        address.fill('address_info', address_info)
        address.hide('USid')
        return Success(data=address)
