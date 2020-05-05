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


class ActivityStatus(Enum):
    close = -10, '已关闭'
    ready = 0, '未开始'
    over = 10, '已结束'


class UserActivityStatus(Enum):
    ready = 0, '待开始'
    comment = 10, '待评价'
    reviewed = 20, '已评价'


class ApplyStatus(Enum):
    reject = -10, '未通过'
    waiting = 0, '待审核'
    passed = 10, '已通过'


class ApproveAction(Enum):
    agree = 10, '通过'
    reject = -10, '拒绝'


class AssistancePictureType(Enum):
    diagnosis = 1, '诊断证明'
    poverty = 2, '特困证明'


class ReviewStatus(Enum):
    classes = 401, "课程"
    register = 402, "挂诊"
    activity = 403, "活动"
    example = 404, "案例"
    video = 405, "视频"


class CouponStatus(Enum):
    use = 501, "可领取"
    end = 502, "已结束"


class CouponUserStatus(Enum):
    had_use = 601, "已经使用"
    not_use = 602, "优惠折扣"
    had_delete = 603, "已经过期"
    cannot_use = 605, "不能使用"


class ConsultationStatus(Enum):
    ready = 0, '未开始'
    # ongoing = 1, '会诊中'
    finish = 2, '已结束'
    # abort = 10, '中止'


class ProductStatus(Enum):
    usual = 0, '上架'
    auditing = 10, '新增'
    delete = 30, '删除'
    sell_out = 40, '售罄'
    off_shelves = 60, '下架'


class ProductType(Enum):
    product = 0, '正常商品'
    coupon = 1, '优惠券'
    package = 2, '套餐'


class OrderMainStatus(Enum):
    wait_pay = 0, '待支付'
    ready = 30, '已完成'
    send = 60, '已发货'
    cancle = -40, '已取消'


class OrderPayType(Enum):
    wx = 0, '微信'
    mix = 5, '组合支付'
    integral = 10, '积分'


class OrderMainType(Enum):
    product = 0, '积分商城商品'
    setmeal = 1, '课时套餐'


class PointTaskType(Enum):
    login = 701, '登录'
    invate_new = 702, '邀请新用户'
    fill_me = 703, '完善个人信息'
    fill_family = 704, '完善家人信息'
    buy_vip = 705, '购买VIP'
    vip_money = 706, '充值'
    watch_video = 707, '看视频'
    register = 708, '挂号'
    review = 709, '评论'
    buy_product = 710, '积分购物'
    make_activity = 711, '报名活动'
    help_someone = 712, '报名公益援助'
    make_evaluation = 713, '参加健康评测'
    reget_point = 714, '积分退还'
    shopping_pay = 715, '购物支出'


if __name__ == '__main__':
    print(CourseStatus(101).zh_value)
