from flask import request
from hospital.extensions.error_response import AuthorityError


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
