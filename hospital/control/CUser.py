"""
本文件用于处理用户相关操作
create user: wiilz
last update time:2020/3/20 23:30
"""
import os
import uuid
import requests
from datetime import datetime
from sqlalchemy import false
from flask import current_app

from hospital.common.default_head import GithubAvatarGenerator
from hospital.config.secret import MiniProgramAppId, MiniProgramAppSecret
from hospital.extensions.error_response import WXLoginError, ParamsError, NotFound
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db
from hospital.extensions.success_response import Success
from hospital.extensions.token_handler import usid_to_token
from hospital.extensions.weixin import WeixinLogin
from hospital.models import User


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
        data = {'token': token, 'usname': user.USname}
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
    def _get_path(self, fold):
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
        data = parameter_required()
        tel = data.get('ustelphone')
        user = User.query.filter(User.isdelete == false(), User.UStelphone == tel).first()
        if not user:
            raise NotFound
        token = usid_to_token(user.USid, model='User', username=user.USname)
        return Success(data={'token': token, 'usname': user.USname})
