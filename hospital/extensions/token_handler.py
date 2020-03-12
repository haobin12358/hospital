# -*-coding: utf-8 -*-
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from .error_response import AuthorityError


def usid_to_token(id, model='User', level=0, expiration='', username='none'):
    """生成令牌
    id: 用户id
    model: 用户类型(User 或者 Admin, Supplizer)
    expiration: 过期时间, 在config/secret中修改
    """
    if not expiration:
        expiration = current_app.config['TOKEN_EXPIRATION']
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({
        'username': username,
        'id': id,
        'model': model,
        'level': level,

    }).decode()

def is_admin():
    """是否是管理员"""
    return hasattr(request, 'user') and request.user.model == 'Admin'

def is_hign_level_admin():
    """超级管理员"""
    return is_admin() and request.user.level == 1

def admin_required(func):
    def inner(self, *args, **kwargs):
        if not is_admin():
            raise AuthorityError()
        return func(self, *args, **kwargs)

    return inner

def is_doctor():
    """医生"""
    return hasattr(request, "user") and request.user.model == "Doctor"

def doctor_required(func):
    def inner(self, *args, **kwargs):
        if not is_doctor():
            raise AuthorityError()
        return func(self, *args, **kwargs)

    return inner
