# -*- coding: utf-8 -*-
from flask import current_app
from sqlalchemy import false, or_
from datetime import timedelta, datetime
from hospital.config.enums import ActivityStatus, UserActivityStatus, OrderMainStatus, CourseStatus, CouponStatus, \
    CouponUserStatus, ProductType, ProductStatus, RegisterStatus
from hospital.extensions.register_ext import celery, db, conn
from hospital.models import Activity, UserActivity, OrderMain, Course, Coupon, CouponUser, Products, Register


def add_async_task(func, start_time, func_args, conn_id=None, queue='high_priority'):
    """
    添加异步任务
    func: 任务方法名 function
    start_time: 任务执行时间 datetime
    func_args: 函数所需参数 tuple
    conn_id: 要存入redis的key
    """
    task_id = func.apply_async(args=func_args, eta=start_time - timedelta(hours=8), queue=queue)
    connid = conn_id if conn_id else str(func_args[0])
    current_app.logger.info(f'add async task: func_args:{func_args} | connid: {conn_id}, task_id: {task_id}')
    conn.set(connid, str(task_id))
    if func_args == 'auto_cancle_order':
        conn.expire(connid, 1850)


def cancel_async_task(conn_id):
    """
    取消已存在的异步任务
    conn_id: 存在于redis的key
    """
    exist_task_id = conn.get(conn_id)
    if exist_task_id:
        exist_task_id = str(exist_task_id, encoding='utf-8')
        celery.AsyncResult(exist_task_id).revoke()
        conn.delete(conn_id)
        current_app.logger.info(f'取消任务成功 task_id:{exist_task_id}')


@celery.task()
def change_activity_status(acid):
    current_app.logger.info(">>> 更改活动状态 acid:{} <<<".format(acid))
    instance_list = []
    try:
        activity = Activity.query.filter(Activity.isdelete == false(), Activity.ACid == acid).first()
        if not activity:
            current_app.logger.error('acid: {} 不存在'.format(acid))
            return
        with db.auto_commit():
            activity.update({'ACstatus': ActivityStatus.over.value})
            instance_list.append(activity)
            user_activitys = UserActivity.query.filter(UserActivity.isdelete == false(),
                                                       UserActivity.ACid == activity.ACid,
                                                       UserActivity.UAstatus == UserActivityStatus.ready.value).all()
            current_app.logger.info('该活动共 {} 条参与记录'.format(len(user_activitys) if user_activitys else 0))
            for ua in user_activitys:
                ua.update({'UAstatus': UserActivityStatus.comment.value})
                instance_list.append(ua)
            db.session.add_all(instance_list)
        conn.delete('start_activity{}'.format(acid))
    except Exception as e:
        current_app.logger.error('Error: {}'.format(e))
    finally:
        current_app.logger.info('>>> 共修改 {} 天记录 <<<'.format(len(instance_list)))
        current_app.logger.info('>>> 修改活动状态结束 acid:{} <<<'.format(acid))


@celery.task()
def change_course_status(coid, end=False):
    current_app.logger.info(">>> 更改课程排班状态 coid:{} <<<".format(coid))
    try:
        with db.auto_commit():
            course = Course.query.filter(Course.isdelete == false(), Course.COid == coid).first()
            if not course:
                current_app.logger.error('未找到该排班')
                return
            if not end:  # 开始课程
                if course.COstatus != CourseStatus.not_start.value:
                    current_app.logger.error('排班状态不为101, COstatus: {}'.format(course.COstatus))
                    return
                course.update({'COstatus': CourseStatus.had_start.value})
                current_app.logger.info('COstatus: 101 --> 102')
                conn_id = 'start_course{}'.format(coid)
            else:  # 结束课程
                if course.COstatus != CourseStatus.had_start.value:
                    current_app.logger.error('排班状态不为102, COstatus: {}'.format(course.COstatus))
                    return
                course.update({'COstatus': CourseStatus.had_end.value})
                current_app.logger.info('COstatus: 102 --> 103')
                conn_id = 'end_course{}'.format(coid)
            db.session.add(course)
        conn.delete(conn_id)
    except Exception as e:
        current_app.logger.error('Error: {}'.format(e))
    finally:
        current_app.logger.info(">>> 更改课程排班状态, 任务结束 coid:{} <<<".format(coid))


@celery.task()
def change_coupon_status(coid):
    current_app.logger.info(">>> 更改优惠券状态 coid:{} <<<".format(coid))
    instance_list = []
    try:
        with db.auto_commit():
            coupon = Coupon.query.filter(Coupon.isdelete == false(), Coupon.COid == coid).first()
            if not coupon:
                current_app.logger.error('未找到该优惠券信息')
                return
            if coupon.COstatus != CouponStatus.use.value:
                current_app.logger.error('状态不正确, COstatus: {}'.format(coupon.COstatus))
                return

            coupon.update({'COstatus': CouponStatus.end.value})
            current_app.logger.info('COstatus: 501 --> 502')
            instance_list.append(coupon)

            user_coupons = CouponUser.query.filter(CouponUser.isdelete == false(), CouponUser.COid == coid,
                                                   CouponUser.UCalreadyuse == CouponUserStatus.not_use.value
                                                   ).all()
            current_app.logger.info('该优惠券共 {} 条领取未使用记录'.format(len(user_coupons) if user_coupons else 0))
            for us_coupon in user_coupons:
                us_coupon.update({'UCalreadyuse': CouponUserStatus.had_delete.value})
                instance_list.append(us_coupon)
            db.session.add_all(instance_list)

            # 同时下架仅用于该优惠券购买的商品
            coupon_products = Products.query.filter(Products.isdelete == false(),
                                                    Products.COid == coid,
                                                    Products.PRtype == ProductType.coupon.value,
                                                    Products.PRstatus == ProductStatus.usual.value
                                                    ).update({'PRstatus': ProductStatus.off_shelves.value})
            current_app.logger.info('同时下架 {} 款商品'.format(len(coupon_products) if coupon_products else 0))

        conn.delete('end_coupon{}'.format(coid))
    except Exception as e:
        current_app.logger.error('Error: {}'.format(e))
    finally:
        current_app.logger.info(">>> 更改优惠券状态任务结束 coid:{} <<<".format(coid))


@celery.task()
def auto_cancle_order(omid):
    from ..control.COrder import COrder
    order_main = OrderMain.query.filter(OrderMain.isdelete == False,
                                        OrderMain.OMstatus == OrderMainStatus.wait_pay.value,
                                        OrderMain.OMid == omid).first()
    if not order_main:
        current_app.logger.info('订单已支付或已取消')
        return
    current_app.logger.info('订单自动取消{}'.format(dict(order_main)))
    corder = COrder()
    corder._cancle(order_main)


@celery.task(name='auto_cancle_register')
def auto_cancle_register():
    now = datetime.now()
    current_app.logger.info('开始取消今日预约 {}'.format(now))
    try:
        with db.auto_commit():
            updatenum = Register.query.filter(
                Register.isdelete == 0,
                Register.REstatus < RegisterStatus.commenting.value,
                or_((Register.REdate == now.date(), Register.REtansferDate == None),
                    Register.REtansferDate == now.date()),
            ).update({'REstatus': RegisterStatus.cancle.value}, synchronize_session=False)
            current_app.logger.info('修改预约{}条'.format(updatenum))
    except Exception as e:
        current_app.logger.error('Error: {}'.format(e))


if __name__ == '__main__':
    from hospital import create_app

    app = create_app()
    with app.app_context():
        change_activity_status()
