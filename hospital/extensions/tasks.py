# -*- coding: utf-8 -*-
from flask import current_app
from sqlalchemy import false
from datetime import timedelta
from hospital.config.enums import ActivityStatus, UserActivityStatus
from hospital.extensions.register_ext import celery, db, conn
from hospital.models import Activity, UserActivity


def add_async_task(func, start_time, func_args, conn_id=None):
    """
    添加异步任务
    func: 任务方法名 function
    start_time: 任务执行时间 datetime
    func_args: 函数所需参数 tuple
    conn_id: 要存入redis的key
    """
    task_id = func.apply_async(args=func_args, eta=start_time - timedelta(hours=8))
    connid = conn_id if conn_id else str(func_args[0])
    current_app.logger.info('add async task: func_args:{} | connid: {}, task_id: {}'.format(func_args, connid, task_id))
    conn.set(connid, str(task_id))


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
        current_app.logger.info('取消任务成功 task_id:{}'.format(exist_task_id))


@celery.task()
def change_activity_status(acid):
    current_app.logger.info(">>> 更改活动状态 acid:{} <<<".format(acid))
    try:
        activity = Activity.query.filter(Activity.isdelete == false(), Activity.ACid == acid).first()
        instance_list = []
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
    except Exception as e:
        current_app.logger.error('Error: {}'.format(e))
    finally:
        current_app.logger.info('>>> 共修改 {} 天记录 <<<'.format(len(instance_list)))
        current_app.logger.info('>>> 修改活动状态结束 acid:{} <<<'.format(acid))


if __name__ == '__main__':
    from hospital import create_app

    app = create_app()
    with app.app_context():
        change_activity_status()
