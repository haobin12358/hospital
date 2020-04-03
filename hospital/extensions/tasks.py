# -*- coding: utf-8 -*-
from flask import current_app
from sqlalchemy import false

from hospital.config.enums import ActivityStatus, UserActivityStatus
from hospital.extensions.register_ext import celery, db
from hospital.models import Activity, UserActivity


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
