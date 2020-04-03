"""
本文件用于处理活动添加，编辑等操作
create user: wiilz
last update time:2020/04/03 01:09
"""
import uuid
from datetime import datetime
from sqlalchemy import false
from flask import current_app, request
from hospital.config.enums import ActivityStatus, UserActivityStatus
from hospital.config.timeformat import format_for_web_second
from hospital.extensions.error_response import ParamsError, StatusError, TokenError
from hospital.extensions.interface.user_interface import is_user, admin_required, is_anonymous, token_required, is_admin
from hospital.extensions.params_validates import parameter_required, validate_datetime
from hospital.extensions.register_ext import db
from hospital.extensions.success_response import Success
from hospital.models import Activity, UserActivity, User


class CActivity(object):

    @admin_required
    def set_activity(self):
        """管理员 添加/编辑活动"""
        data = request.json
        acstarttime, acnumber = data.get('acstarttime'), data.get('acnumber')
        acid = data.get('acid')
        time_now = datetime.now()
        if acstarttime and not validate_datetime(acstarttime):
            raise ParamsError('活动时间格式错误')
        acstarttime = datetime.strptime(acstarttime, format_for_web_second) if acstarttime else None
        if acstarttime and acstarttime <= time_now:
            raise ParamsError('活动时间应大于当前时间')
        if acnumber and (not str(acnumber).isdigit() or int(acnumber) == 0):
            raise ParamsError('活动人数应为大于0的整数')
        required_dict = {'acname': '活动名称', 'acbanner': '活动图片', 'acorganizer': '举办人',
                         'acstarttime': '活动时间', 'aclocation': '活动地点', 'acdetail': '活动介绍',
                         'acnumber': '活动人数'}
        ac_dict = {'ACname': data.get('acname'), 'ACbanner': data.get('acbanner'),
                   'ACorganizer': data.get('acorganizer'), 'ACstartTime': acstarttime,
                   'AClocation': data.get('aclocation'), 'ACdetail': data.get('acdetail'),
                   'ACnumber': acnumber
                   }
        with db.auto_commit():
            if not acid:
                if Activity.query.filter(Activity.isdelete == false(), Activity.ACname == data.get('acname'),
                                         Activity.ACstartTime == acstarttime).first():
                    raise ParamsError('您已添加过 {} 活动'.format(data.get('acname')))
                parameter_required(required_dict, datafrom=data)
                ac_dict['ACid'] = str(uuid.uuid1())
                ac_dict['ADid'] = getattr(request, 'user').id
                ac_dict['ACstatus'] = ActivityStatus.ready.value
                activity = Activity.create(ac_dict)
                msg = '添加成功'
                # todo 异步任务
            else:
                activity = Activity.query.filter(Activity.isdelete == false(),
                                                 Activity.ACid == acid).first_('活动不存在')
                self._can_activity_edit(activity)
                if data.get('delete'):
                    activity.update({'isdelete': True})
                    msg = '删除成功'
                else:
                    parameter_required(required_dict, datafrom=data)
                    activity.update(ac_dict)
                    msg = '更新成功'
            db.session.add(activity)
            return Success(message=msg, data={'acid': activity.ACid})

    def _can_activity_edit(self, activity):
        if activity.ACstatus == ActivityStatus.over.value:
            raise StatusError('已结束的活动暂不能进行编辑')
        if self._ua_filter([UserActivity.ACid == activity.ACid,
                            UserActivity.UAstatus == UserActivityStatus.ready.value],
                           ).first():
            raise StatusError('活动已有报名人员，咱不能进行编辑')

    def list_activity(self):
        """首页活动展示 / 我的活动"""
        args = parameter_required(('page_size', 'page_num'))
        option = args.get('option')
        time_now = datetime.now()
        if option == 'my':
            return self._query_my_activity()
        filter_args = []
        if is_anonymous() or is_user():
            filter_args.extend([Activity.ACstatus == ActivityStatus.ready.value,
                                Activity.ACstartTime > time_now])
        ac_list = Activity.query.filter(Activity.isdelete == false(), *filter_args
                                        ).order_by(Activity.ACstatus.asc(),
                                                   Activity.ACstartTime.desc()).all_with_page()
        for ac in ac_list:
            ac.fields = ['ACid', 'ACname', 'ACbanner']
            ac.fill('acstatus_zh', ActivityStatus(ac.ACstatus).zh_value)
            if filter_args:
                remain = ac.ACstartTime - time_now
                remain_day = remain.days
                remain_str = f'{remain.seconds // 3600}小时' if (
                        remain.seconds // 3600) else f'{(remain.seconds % 3600) // 60}分钟' if (
                        (remain.seconds % 3600) // 60) else f'{remain.seconds}秒'
                ac.fill('remain_time', f'{remain_day}天' if remain_day else remain_str)
            if is_admin():
                ac.fill('signed_number', self._ua_filter([UserActivity.ACid == ac.ACid, ]).count())
        return Success(data=ac_list)

    def _query_my_activity(self):
        if not is_user():
            raise TokenError
        uas = self._ua_filter([UserActivity.USid == getattr(request, 'user').id]).all_with_page()
        ac_list = []
        for ua in uas:
            activity = Activity.query.filter(Activity.ACid == ua.ACid).first()
            if not activity:
                current_app.logger.error('activity not found: acid:{}'.format(ua.ACid))
                continue
            activity.fields = ['ACid', 'ACname', 'ACbanner']
            activity.fill('uastatus_zh', UserActivityStatus(ua.UAstatus).zh_value)
            activity.fill('uaid', ua.UAid)
            ac_list.append(activity)
        return Success(data=ac_list)

    def info(self):
        """活动详情"""
        args = request.args.to_dict()
        uaid = args.get('uaid')
        if uaid:
            ua = self._ua_filter((UserActivity.UAid == uaid,), ).first_('活动不存在')
            acid = ua.ACid
        else:
            parameter_required('acid', datafrom=args)
            acid = args.get('acid')
        activity = Activity.query.filter(Activity.isdelete == false(),
                                         Activity.ACid == acid).first_('未找到活动信息')
        if not is_admin():
            activity.hide('ACnumber')
        activity.fill('acstatus_zh', ActivityStatus(activity.ACstatus).zh_value)
        activity.fill('remain_people', self._query_activity_remain_people(activity))
        return Success(data=activity)

    @staticmethod
    def _ua_filter(filter_args):
        return UserActivity.query.filter(UserActivity.isdelete == false(), *filter_args)

    def _query_activity_remain_people(self, activity):
        return activity.ACnumber - (self._ua_filter([UserActivity.ACid == activity.ACid, ]).count())

    @admin_required
    def signed_up(self):
        """查看已报名人员"""
        args = parameter_required('acid')
        users = User.query.join(UserActivity, UserActivity.USid == User.USid
                                ).filter(UserActivity.isdelete == false(),
                                         UserActivity.ACid == args.get('acid')
                                         ).all_with_page()
        for user in users:
            user.fields = ['USid', 'USname', 'USavatar', 'USgender', 'UStelphone']
        return Success(data=users)

    def sign_up(self):
        """用户报名"""
        if not is_user():
            raise TokenError
        data = parameter_required('acid')
        usid = getattr(request, 'user').id
        activity = Activity.query.filter(Activity.isdelete == false(),
                                         Activity.ACstatus == ActivityStatus.ready.value,
                                         Activity.ACstartTime >= datetime.now(),
                                         Activity.ACid == data.get('acid')).first_('活动已结束或不存在')
        if self._ua_filter([UserActivity.USid == usid, UserActivity.ACid == activity.ACid]).first():
            raise StatusError('您已报名过该活动')
        if self._query_activity_remain_people(activity) <= 0:
            raise StatusError('该活动报名人数已满，请期待下次活动')
        with db.auto_commit():
            ua = UserActivity.create({'UAid': str(uuid.uuid1()),
                                      'USid': usid,
                                      'ACid': activity.ACid,
                                      'UAstatus': UserActivityStatus.ready.value})
            db.session.add(ua)
        return Success('报名成功', data={'uaid': ua.UAid})
