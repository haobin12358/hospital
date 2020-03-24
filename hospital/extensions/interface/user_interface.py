from flask import request
from hospital.extensions.error_response import AuthorityError, TokenError


def is_anonymous():
    """是否是游客"""
    return not hasattr(request, 'user')


def is_user():
    """是否是普通用户"""
    return hasattr(request, 'user') and request.user.model == 'User'


def token_required(func):
    def inner(self, *args, **kwargs):
        if not is_anonymous():
            return func(self, *args, **kwargs)
        raise TokenError()

    return inner


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
