# -*- coding: utf-8 -*-
import os
import re
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
            # setattr(request, 'user', user)
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


def request_first_handler(app):
    @app.before_request
    def token_to_user():
        current_app.logger.info('>>>>>>>>\n>>>>>>>>{}<<<<<<<<\n<<<<<<<<<<'.format('before request'))
        parameter = request.args.to_dict()
        token = parameter.get('token')
        token_to_user_(token)


def error_handler(app):
    @app.errorhandler(Exception)
    def framework_error(e):
        if isinstance(e, Success):
            return e
        current_app.logger.error(e)
        if isinstance(e, BaseError):
            return e
        else:
            if app.config['DEBUG']:
                return SystemError(e.args)
            return SystemError()
