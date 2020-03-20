"""
本文件用于处理课程及课程预约相关逻辑处理
create user: haobin12358
last update time:2020/3/20 12:23
"""
import uuid
from flask import request, current_app
from hospital.extensions.interface.user_interface import admin_required
from hospital.extensions.register_ext import db
from hospital.extensions.interface.user_interface import is_doctor
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError
from hospital.models.departments import Doctor
from hospital.models.classes import Classes, Course, Subscribe
from hospital.models.user import User


class CClasses:

    @admin_required
    def set_class(self):
        """
        创建/编辑/删除课程
        """
        return Success()