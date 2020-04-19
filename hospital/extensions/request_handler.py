# -*- coding: utf-8 -*-
import re
import traceback
import base64
from collections import namedtuple
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from flask import current_app, request
from .error_response import BaseError, SystemError
from .success_response import Success


def token_to_user_(token):
    user = None
    if token:
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
            id = data['id']
            model = data['model']
            level = data['level']
            username = data.get('username', 'none')
            User = namedtuple('User', ('id', 'model', 'level', 'username'))
            user = User(id, model, level, username)
            setattr(request, 'user', user)
            current_app.logger.info('current_user info : {}'.format(data))
        except BadSignature as e:
            pass
        except SignatureExpired as e:
            pass
        except Exception as e:
            current_app.logger.info(e)
    current_app.logger.info(request.detail)
    return user


def _get_user_agent():
    user_agent = request.user_agent
    ua = str(user_agent).split()
    osversion = phonemodel = wechatversion = nettype = None
    if not re.match(r'^(android|iphone)$', str(user_agent.platform)):
        return
    for index, item in enumerate(ua):
        if 'Android' in item:
            osversion = f'Android {ua[index + 1][:-1]}'
            phonemodel = ua[index + 2]
            temp_index = index + 3
            while 'Build' not in ua[temp_index]:
                phonemodel = f'{phonemodel} {ua[temp_index]}'
                temp_index += 1
        elif 'OS' in item:
            if ua[index - 1] == 'iPhone':
                osversion = f'iOS {ua[index + 1]}'
                phonemodel = 'iPhone'
        if 'MicroMessenger' in item:
            try:
                wechatversion = item.split('/')[1]
                if '(' in wechatversion:
                    wechatversion = wechatversion.split('(')[0]
            except Exception as e:
                current_app.logger.error('MicroMessenger:{}, error is :{}'.format(item, e))
                wechatversion = item.split('/')[1][:3]
        if 'NetType' in item:
            nettype = re.match(r'^(.*)\/(.*)$', item).group(2)
    return osversion, phonemodel, wechatversion, nettype, user_agent.string


def _invitation_records():
    secret_user_id = request.args.to_dict().get('secret_usid')
    if not secret_user_id:
        return
    from hospital.extensions.interface.user_interface import is_user
    if not is_user():
        return
    current_app.logger.info('>>>>>>>>record invitation<<<<<<<<')
    try:
        inviter_id = base_decode(secret_user_id)
        current_app.logger.info(f'secret_usid --> inviter_id: {inviter_id}')
    except Exception as e:
        current_app.logger.error(f'解析secret_usid时出错： {e}')
        return
    usid = getattr(request, 'user').id
    if inviter_id == usid:
        current_app.logger.info('inviter == invitee')
        return
    from hospital.models.user import UserInvitation
    from hospital.extensions.register_ext import db
    import uuid
    try:
        with db.auto_commit():
            uin = UserInvitation.create({
                'UINid': str(uuid.uuid1()),
                'USInviter': inviter_id,
                'USInvitee': usid,
                'UINapi': request.path
            })
            current_app.logger.info(f'{request.path} 创建邀请记录')
            db.session.add(uin)
    except Exception as e:
        current_app.logger.error(f'存储邀请记录时出错： {e}')


def base_decode(raw):
    decoded = base64.b64decode(raw + '=' * (4 - len(raw) % 4)).decode()
    return decoded


def base_encode(raw):
    import base64
    raw = raw.encode()
    return base64.b64encode(raw).decode()


def request_first_handler(app):
    @app.before_request
    def token_to_user():
        current_app.logger.info('>>>>>>>>\n>>>>>>>>{}<<<<<<<<\n<<<<<<<<<<'.format('before request'))
        parameter = request.args.to_dict()
        token = parameter.get('token')
        token_to_user_(token)

    @app.before_request
    def invitation_records():
        _invitation_records()


def error_handler(app):
    @app.errorhandler(Exception)
    def framework_error(e):
        if isinstance(e, Success):
            return e
        if isinstance(e, Exception):
            data = traceback.format_exc()
            current_app.logger.error(data)
            # current_app.logger.error(data, exc_info=True)
        if isinstance(e, BaseError):
            return e
        else:
            if app.config['DEBUG']:
                return SystemError(e.args)
            return SystemError()
