"""
本文件用于处理优惠券/积分逻辑处理
create user: haobin12358
last update time:2020/4/3 23:11
"""
import uuid
import datetime
from decimal import Decimal
from flask import request, current_app
from hospital.extensions.register_ext import db
from hospital.extensions.interface.user_interface import is_hign_level_admin, is_admin
from hospital.extensions.success_response import Success
from hospital.extensions.request_handler import token_to_user_
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.error_response import TimeError, AuthorityError
from hospital.models.coupon import Coupon, CouponUser
from hospital.config.enums import CouponStatus, CouponUserStatus

class CWelfare:

    def set_coupon(self):
        """
        创建/编辑/删除优惠券
        """
        if not (is_admin() or is_hign_level_admin()):
            return AuthorityError('无权限')
        data = parameter_required(('costarttime', "coendtime", "cosubtration", "colimitnum")
                                  if not request.json.get('delete') else('coid',))
        if data.get('codownline'):
            codownline = data.get('codownline')
        else:
            codownline = 0
        costarttime = data.get('costarttime')
        coendtime = data.get('coendtime')
        if costarttime:
            start_time = datetime.datetime.strptime(costarttime, "%Y-%m-%d %H:%M:%S")
        else:
            start_time = datetime.datetime.now()
        if coendtime:
            end_time = datetime.datetime.strptime(coendtime, "%Y-%m-%d %H:%M:%S")
        else:
            end_time = datetime.datetime.now()
        co_dict = {
            'COstarttime': costarttime,
            'COendtime': coendtime,
            'COdownline': codownline,
            'COlimitnum': data.get('colimitnum'),
            'COsubtration': Decimal(str(data.get('cosubtration') or 0)),
            'COgetnum': 0
        }
        coid = data.get('coid')
        with db.auto_commit():
            if not coid:
                """新增"""
                if end_time < start_time or datetime.datetime.now() > start_time:
                    return TimeError()
                co_dict['COid'] = str(uuid.uuid1())
                co_dict["COstatus"] = 501
                co_instance = Coupon.create(co_dict)
                msg = '添加成功'
            else:
                """修改/删除"""
                if start_time < datetime.datetime.now() < end_time:
                    return AuthorityError()
                co_instance = Coupon.query.filter(Coupon.COid == coid).first_('未找到该优惠券信息')
                if data.get('delete'):
                    co_instance.update({'isdelete': 1})
                    msg = '删除成功'
                else:
                    co_instance.update(co_dict, null='not')
                    msg = '编辑成功'
            db.session.add(co_instance)
        return Success(message=msg)

    def list(self):
        """
        获取优惠券列表（后台）
        """
        coupon_list = Coupon.query.filter(Coupon.isdelete == 0).order_by(Coupon.createtime.desc()).all_with_page()
        for coupon in coupon_list:
            coupon.fill("costatus_zh", CouponStatus(coupon.COstatus).zh_value)
            if coupon.COdownline == 0:
                coupon.fill("codownline_zh", "无限制")
            else:
                coupon.fill("codownline_zh", "满足{0}元即可使用".format(Decimal(str(coupon.COdownline))))

        return Success(message="获取优惠券列表成功", data=coupon_list)

    def get(self):
        """获取优惠券详情（后台）"""
        args = parameter_required(('token', 'coid', ))
        if not (is_admin() or is_hign_level_admin()):
            return AuthorityError('无权限')
        coupon = Coupon.query.filter(Coupon.isdelete == 0, Coupon.COid == args.get('coid')).first_("未找到该优惠券")
        coupon.fill("costatus_zh", CouponStatus(coupon.COstatus).zh_value)
        return Success(message="获取优惠券信息成功", data=coupon)

    def userlist(self):
        """获取用户优惠券（前台）"""
        args = parameter_required(('token', 'ucalreadyuse', ))
        # 601已使用602未使用603已过期604可使用
        user = token_to_user_(args.get('token'))
        if user.model != "User":
            return AuthorityError()
        usid = user.id
        ucalreadyuse = int(args.get('ucalreadyuse'))
        if ucalreadyuse in [601, 602, 603]:
            coupon_list = CouponUser.query.filter(CouponUser.isdelete == 0, CouponUser.USid == usid,
                                                  CouponUser.UCalreadyuse == ucalreadyuse)\
                .order_by(CouponUser.createtime.desc()).all_with_page()
        elif ucalreadyuse in [604]:
            coupon_list = CouponUser.query.filter(CouponUser.isdelete == 0, CouponUser.USid == usid,
                                                  CouponUser.UCalreadyUse == 602,
                                                  CouponUser.COstarttime < datetime.datetime.now(),
                                                  CouponUser.COendtime > datetime.datetime.now())\
                .order_by(CouponUser.createtime.desc()).all_with_page()
        else:
            coupon_list = []
        for coupon in coupon_list:
            coupon.fill("ucalreadyuse_zh", CouponUserStatus(coupon.UCalreadyuse).zh_value)
            if coupon.COdownline == 0:
                coupon.fill("codownline_zh", "无限制")
            else:
                coupon.fill("codownline_zh", "满足{0}元即可使用".format(Decimal(str(coupon.COdownline))))
            coupon.fill("cotime", "{0}月{1}日-{2}月{3}日".format(coupon.COstarttime.month, coupon.COstarttime.day,
                                                             coupon.COendtime.month, coupon.COendtime.day))

        return Success(message="获取优惠券成功", data=coupon_list)