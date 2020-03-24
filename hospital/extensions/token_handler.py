# -*-coding: utf-8 -*-
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


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
