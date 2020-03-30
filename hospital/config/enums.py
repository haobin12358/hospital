# -*- coding: utf-8 -*-
from hospital.extensions.base_enum import Enum


class TestEnum(Enum):
    ok = 66, '成功'


class DoctorMetiaType(Enum):
    mainpic = 0, '主图'
    listpic = 1, '列表图'
    qrpic = 2, '二维码'


class AdminLevel(Enum):
    super_admin = 1, '超级管理员'
    common_admin = 2, '普通管理员'
    doctor = 3, '医生'


class AdminStatus(Enum):
    normal = 0, '正常'
    frozen = 1, '已冻结'
    deleted = 2, '已删除'


class Gender(Enum):
    man = 1, '男'
    woman = 2, '女'


class CourseStatus(Enum):
    not_start = (101, '未开始')
    had_start = (102, '已开始')
    had_end = (103, '已结束')


class FamilyRole(Enum):
    myself = 1, '本人'
    spouse = 2, '配偶'
    child = 3, '孩子'


class FamilyType(Enum):
    father = 1, '父亲'
    mother = 2, '母亲'
    son = 3, '儿子'
    daughter = 4, '女儿'


class RegisterStatus(Enum):
    queuing = 0, '排队中'
    pending = 1, '待就诊'
    transfer = 2, '被调剂'
    commenting = 3, '待评价'
    complete = 4, '已评价'
    cancle = -1, '未就诊'


class SubscribeStatus(Enum):
    had_subscribe = 201, '已预约'
    had_classof = 202, '已上课'
    had_review = 203, '已评价'


class ApplyStatus(Enum):
    reject = -10, '未通过'
    waiting = 0, '审核中'
    passed = 10, '已通过'


class ApproveAction(Enum):
    agree = 10, '通过'
    reject = -10, '拒绝'


class AssistancePictureType(Enum):
    diagnosis = 1, '诊断证明'
    poverty = 2, '特困证明'


if __name__ == '__main__':
    print(CourseStatus(101).zh_value)
