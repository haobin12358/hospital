# -*- coding: utf-8 -*-
import random
import re
import time
from datetime import datetime, timedelta
from decimal import Decimal

from flask import current_app, request, json
import uuid

from sqlalchemy import or_

from hospital.extensions.base_jsonencoder import JSONEncoder
from hospital.extensions.interface.user_interface import admin_required, token_required, is_user
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, StatusError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db, wx_pay
from hospital.extensions.tasks import add_async_task
from hospital.extensions.weixin.pay import WeixinPayError
from hospital.models import Coupon, Products, Classes, User, OrderMain, CouponUser, UserAddress, AddressProvince, \
    AddressCity, AddressArea, UserIntegral, OrderPay, UserHour, Setmeal
from hospital.config.enums import ProductStatus, ProductType, CouponUserStatus, OrderMainStatus, \
    OrderPayType, OrderMainType, PointTaskType


class COrder(object):
    @token_required
    def list(self):
        data = parameter_required()
        usid = getattr(request, 'user').id
        omstatus = data.get('omstatus')
        omname = data.get('omname')
        omtype = data.get('omtype', 0)
        filter_args = [OrderMain.isdelete == 0, ]
        try:
            omtype = OrderMainType(int(omtype)).value
        except:
            raise ParamsError('订单类型有误 {}'.format(omtype))

        if is_user():
            filter_args.append(OrderMain.OMstatus >= OrderMainStatus.ready.value)
            filter_args.append(OrderMain.OMtype == omtype)
            filter_args.append(OrderMain.USid == usid)
        elif omstatus is not None:
            try:
                omstatus = OrderMainStatus(int(str(omstatus))).value
            except:
                raise ParamsError('订单状态筛选参数异常')
            filter_args.append(OrderMain.OMstatus == omstatus)
        if omname:
            filter_args.append(or_(
                OrderMain.CLname.ilike('%{}%'.format(omname)),
                OrderMain.PRtitle.ilike('%{}%'.format(omname))))

        omlist = OrderMain.query.filter(*filter_args).order_by(OrderMain.createtime.desc()).all_with_page()
        if is_user():
            uh_list = UserHour.query.filter(UserHour.USid == usid, UserHour.isdelete == 0).all()
            # 可用时长统计
            smsum = sum([int(uh.UHnum) for uh in uh_list])
            return Success('获取成功', data={'omlist': omlist, 'smsum': smsum})

        return Success('获取成功', data={'omlist': omlist})

    @admin_required
    def get(self):
        data = parameter_required('omid')
        omid = data.get('omid')
        om = OrderMain.query.filter(OrderMain.OMid == omid, OrderMain.isdelete == 0).first_('订单已删除')
        return Success('获取成功', data=om)

    @token_required
    def create(self):
        data = parameter_required()
        usid = getattr(request, 'user').id
        ucid = data.get('ucid')
        prid = data.get('prid')
        omnum = data.get('omnum', 1)
        uaid = data.get('uaid')
        smid = data.get('smid')
        clid = data.get('clid')
        omtype = data.get('omtype')

        omid = str(uuid.uuid1())

        with db.auto_commit():

            now = datetime.now()

            user = User.query.filter(User.USid == usid, User.isdelete == 0).first_('token过期, 请刷新')
            ua = UserAddress.query.filter(
                UserAddress.UAid == uaid, UserAddress.USid == usid, UserAddress.isdelete == 0).first_('地址已删除')

            apname, acname, aaname = db.session.query(
                AddressProvince.APname, AddressCity.ACname, AddressArea.AAname).filter(
                AddressArea.AAid == ua.AAid, AddressCity.ACid == AddressArea.ACid,
                AddressProvince.APid == AddressCity.APid, ).first()

            omrecvaddress = '{}{}{}{}'.format(apname, acname, aaname, ua.UAtext)

            uc = None
            if ucid:
                # 优惠券是否可用
                uc = CouponUser.query.filter(
                    CouponUser.UCid == ucid, CouponUser.isdelete == 0,
                    CouponUser.COstarttime <= now, CouponUser.COendtime >= now,
                    CouponUser.UCalreadyuse == CouponUserStatus.not_use.value).first_('优惠券已使用')
            # usecoupon = False
            try:
                omnum = int(omnum)
                if omnum <= 0:
                    raise ParamsError('{} 需要是正整数'.format('商品数量'))
            except:
                raise ParamsError('{}需要是整数'.format('商品数量'))

            opayno = wx_pay.nonce_str
            try:
                omtype = OrderMainType(int(str(omtype))).value
            except:
                raise ParamsError('订单创建异常')

            if omtype == OrderMainType.product.value:
                body, truemount, omintegralpayed = self._create_product_order(
                    prid, omid, omnum, user, opayno, ua, omrecvaddress, uc)
            elif omtype == OrderMainType.setmeal.value:
                omintegralpayed = 0
                body, truemount = self._create_setmeal_order(
                    smid, clid, omid, user, uc, omnum, opayno, ua, omrecvaddress)
            else:
                raise ParamsError('订单创建异常')

        from ..extensions.tasks import auto_cancle_order
        # auto_cancle_order.apply_async(args=(omid,), countdown=30 * 60, expires=40 * 60, )
        # todo 修改自动取消为30 minute
        add_async_task(func=auto_cancle_order, start_time=now + timedelta(minutes=30), func_args=(omid,))
        # # 生成支付信息
        # body = product.PRtitle
        openid = user.USopenid

        # todo 修改支付参数获取
        if not truemount:
            pay_type = OrderPayType.integral.value
            pay_args = 'integralpay'
            self._over_ordermain(omid)
        elif not omintegralpayed:
            pay_args = self._pay_detail(opayno, float(truemount), body, openid=openid)
            # pay_args = 'wxpay'
            pay_type = OrderPayType.wx.value
        else:
            # pay_args = self._pay_detail(opayno, float(truemount), body, openid=openid)
            pay_args = 'wxpay'
            pay_type = OrderPayType.mix.value

        response = {
            'paytype': pay_type,
            'args': pay_args
        }
        return Success('下单成功', data=response)

    def wechat_notify(self):
        """微信支付回调"""
        # todo
        pass

    def pay(self):
        """订单发起支付"""
        # todo  前端有了订单列表之后增加该接口用以继续支付
        return

    def _cancle(self, ordermain):
        with db.auto_commit():
            ordermain.OMstatus = OrderMainStatus.cancle.value
            db.session.add(ordermain)
            # 优惠券返回
            if ordermain.UCid:
                uc = CouponUser.query.filter(CouponUser.UCid == ordermain.UCid, CouponUser.isdelete == 0).first()
                if uc:
                    uc.UCalreadyuse = CouponUserStatus.not_use.value
                    db.session.add(uc)
            if ordermain.OMtype == OrderMainType.product.value:
                self._cancle_product(ordermain)
            elif ordermain.OMtype == OrderMainType.setmeal.value:
                self._cancle_setmeal(ordermain)

    def _cancle_product(self, ordermain):
        # 商品库存
        product = Products.query.filter(Products.PRid == ordermain.PRid, Products.isdelete == 0).first()
        if not product:
            return

        product.PRstock += int(ordermain.OMnum)

        if product.PRtype == ProductType.package.value and product.CLid:
            # 收回课时
            uh = UserHour.query.filter(UserHour.USid == ordermain.USid, UserHour.CLid == product.CLid).first()
            if uh:
                now_num = int(uh.SMnum)
                reduce_num = now_num - int(ordermain.SMnum) * int(ordermain.OMnum)
                uh.SMnum = reduce_num if reduce_num >= 0 else 0
        if product.PRtype == ProductType.coupon.value and product.COid:
            # 收回优惠券
            CouponUser.query.filter(
                CouponUser.OMid == ordermain.OMid, CouponUser.isdelete == 0).delete_(synchronize_session=False)
        if ordermain.OMintegralpayed:
            # 714 积分退还
            user = User.query.filter(User.USid == ordermain.USid, User.isdelete == 0).first()
            if user:
                user.USintegral = int(user.USintegral) + int(ordermain.OMintegralpayed)
                db.session.add(UserIntegral.create({
                    'UIid': str(uuid.uuid1()),
                    'USid': user.USid,
                    'UIintegral': ordermain.OMintegralpayed,
                    'UIaction': 714,  # todo 修改为enum
                    'UItype': 3,
                    'UItrue': 1,
                }))

    def _cancle_setmeal(self, ordermain):
        # 收回课时
        uh = UserHour.query.filter(UserHour.USid == ordermain.USid, UserHour.CLid == ordermain.CLid).first()
        if uh:
            now_num = int(uh.SMnum)
            reduce_num = now_num - int(ordermain.SMnum) * int(ordermain.OMnum)
            uh.SMnum = reduce_num if reduce_num >= 0 else 0

    @staticmethod
    def _generic_omno():
        """生成订单号"""
        return str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))) + \
               str(time.time()).replace('.', '')[-7:] + str(random.randint(1000, 9999))

    def _pay_detail(self, opayno, mount_price, body, openid='openid'):

        body = re.sub("[\s+\.\!\/_,$%^*(+\"\'\-_]+|[+——！，。？、~@#￥%……&*（）]+", '', body)
        mount_price = 0.01  # todo 上线后修改为实际支付
        current_app.logger.info('openid is {}, out_trade_no is {} '.format(openid, opayno))

        try:
            body = body[:16] + '...'
            current_app.logger.info('body is {}, wechatpay'.format(body))
            wechat_pay_dict = {
                'body': body,
                'out_trade_no': opayno,
                'total_fee': int(mount_price * 100),
                'attach': 'attach',
                'spbill_create_ip': request.remote_addr
            }

            if not openid:
                raise StatusError('用户未使用微信登录')
            # wechat_pay_dict.update(dict(trade_type="JSAPI", openid=openid))
            wechat_pay_dict.update({
                'trade_type': 'JSAPI',
                'openid': openid
            })
            raw = wx_pay.jsapi(**wechat_pay_dict)

        except WeixinPayError as e:
            raise SystemError('微信支付异常: {}'.format('.'.join(e.args)))

        current_app.logger.info('pay response is {}'.format(raw))
        return raw

    def _create_product_order(self, prid, omid, omnum, user, opayno, ua, omrecvaddress, uc):
        decimal_omnum = Decimal(omnum)

        product = Products.query.filter(Products.PRid == prid,
                                        Products.PRstatus == ProductStatus.usual.value).first_('商品已售空')
        mount = Decimal(product.PRprice if product.PRprice else 0) * decimal_omnum
        omintegral = int(product.PRintegral if product.PRintegral else 0) * omnum
        omintegralunit = product.PRvipIntegral if user.USlevel and product.PRvipIntegral else product.PRvipIntegral
        omintegralpayed = int(omintegralunit if omintegralunit else 0) * omnum
        if omintegralpayed:
            if omintegralpayed > int(user.USintegral):
                # todo 增加积分兑换规则
                raise ParamsError('用户积分不足')
            user.USintegral = int(user.USintegral) - omintegralpayed
            # 创建积分修改记录
            ui = UserIntegral.create({
                'UIid': str(uuid.uuid1()),
                'USid': user.USid,
                'UIintegral': omintegralpayed,
                'UIaction': PointTaskType.shopping_pay.value,
                'UItype': 2,
                'UItrue': 0,
            })
            # 积分消费流水
            op_integral = OrderPay.create({
                'OPayid': str(uuid.uuid1()),
                'OPayno': opayno,
                'OPayType': OrderPayType.integral.value,
                'OPayMount': omintegralpayed,
            })
            db.session.add(ui)
            db.session.add(op_integral)
            db.session.add(user)

        trueunit = product.PRvipPrice if user.USlevel and product.PRvipPrice else product.PRprice

        truemount = (Decimal(trueunit) if trueunit else Decimal(0)) * decimal_omnum
        ucid = ''
        if uc:
            if uc.COdownline and truemount >= Decimal(uc.COdownline):
                # 优惠后价格
                truemount = truemount - Decimal(uc.COsubtration)
                if truemount < Decimal(0):
                    truemount = Decimal(0)
                uc.UCalreadyuse = CouponUserStatus.had_use.value
                db.session.add(uc)
                ucid = uc.UCid

            else:
                raise ParamsError('商品价格达不到优惠券最低金额')
        omstatus = OrderMainStatus.wait_pay.value
        if not truemount:
            omstatus = OrderMainStatus.ready.value
        content = ''
        if product.COid and product.PRtype == ProductType.coupon.value:
            # 优惠券商品 记录优惠券信息
            coupon = Coupon.query.filter(Coupon.COid == product.COid, Coupon.isdelete == 0).first_('商品已售空')
            content = json.dumps(coupon, cls=JSONEncoder)
            custatus = CouponUserStatus.cannot_use.value
            if omstatus == OrderMainStatus.ready.value:
                custatus = CouponUserStatus.not_use.value
            model_list = []
            for _ in range(omnum):
                couponuser = CouponUser.create({
                    'UCid': str(uuid.uuid1()),
                    'COid': product.COid,
                    'USid': user.USid,
                    'COsubtration': coupon.COsubtration,
                    'COstarttime': coupon.COstarttime,
                    'COendtime': coupon.COendtime,
                    'COdownline': coupon.COdownline,
                    'UCalreadyuse': custatus,
                    'OMid': omid
                })
                model_list.append(couponuser)
            db.session.add_all(model_list)

        if product.CLid and product.PRtype == ProductType.package.value:
            self._increase_smnum(user.USid, product.CLid, product.SMnum, omnum, omstatus)
            classes = Classes.query.filter(Classes.CLid == product.CLid, Classes.isdelete == 0).first_('商品已售空')
            content = json.dumps(classes, cls=JSONEncoder)

        # 库存修改
        product.PRstock -= omnum

        om = OrderMain.create({
            'OMid': omid,
            'OMno': self._generic_omno(),
            'USid': user.USid,
            'UCid': ucid,
            'OPayno': opayno,
            'OMmount': mount,
            'OMtrueMount': truemount,
            'OMstatus': omstatus,
            'OMrecvPhone': ua.UAtel,
            'OMrecvName': ua.UAname,
            'OMrecvAddress': omrecvaddress,
            'OMintegralpayed': omintegralpayed,
            'OMintegral': omintegral,
            'PRid': prid,
            'PRtype': product.PRtype,
            'PRprice': product.PRprice,
            'PRintegral': product.PRintegral,
            'SMnum': product.SMnum,
            'PRtitle': product.PRtitle,
            'PRmedia': product.PRmedia,
            'PRcontent': content,
            'OMnum': omnum,
            'OMtype': OrderMainType.product.value,
        })
        if truemount:
            op_instance = OrderPay.create({
                'OPayid': str(uuid.uuid1()),
                'OPayno': opayno,
                'OPayType': OrderPayType.wx.value,
                'OPayMount': truemount,
            })
            db.session.add(op_instance)
        db.session.add(om)
        return product.PRtitle, truemount, omintegralpayed

    def _increase_smnum(self, usid, clid, smnum, omnum, omstatus):
        uh = UserHour.query.filter(UserHour.USid == usid, UserHour.CLid == clid, UserHour.isdelete == 0).first()
        add_smnum = int(smnum) * int(omnum)
        uhnum = 0
        if omstatus == OrderMainStatus.ready.value:
            uhnum = add_smnum
        if uh:
            uh.SMnum += add_smnum
            uh.UHnum += uhnum
        else:
            uh = UserHour.create({
                'UHid': str(uuid.uuid1()),
                'USid': usid,
                'CLid': clid,
                'SMnum': add_smnum,
                'UHnum': uhnum
            })
        db.session.add(uh)

    def _create_setmeal_order(self, smid, clid, omid, user, uc, omnum, opayno, ua, omrecvaddress):
        decimal_omnum = Decimal(omnum)
        if smid != '1':
            sm = Setmeal.query.join(Classes, Classes.CLid == Setmeal.CLid).filter(
                Setmeal.SMid == smid, Setmeal.CLid == clid,
                Setmeal.isdelete == 0, Classes.isdelete == 0).first_('课时套餐已下架')
            smnum = sm.SMnum
            clname = sm.CLname
            trueunit = (Decimal(sm.SMprice) if sm.SMprice else Decimal(0))
        else:
            cl = Classes.queury.filter(Classes.CLid == clid, Classes.isdelete == 0).first_('课程已结束')
            # trueunit = sm.SMprice
            trueunit = (Decimal(cl.CLprice) if cl.CLprice else Decimal(0))
            smnum = 1
            clname = cl.CLname

        mount = truemount = trueunit * decimal_omnum
        ucid = ''
        if uc:
            if uc.COdownline and truemount >= Decimal(uc.COdownline):
                # 优惠后价格
                truemount = truemount - Decimal(uc.COsubtration)
                if truemount < Decimal(0):
                    truemount = Decimal(0)
                uc.UCalreadyuse = CouponUserStatus.had_use.value
                ucid = uc.UCid
                db.session.add(uc)

            else:
                raise ParamsError('商品价格达不到优惠券最低金额')
        omstatus = OrderMainStatus.wait_pay.value

        if truemount == 0:
            omstatus = OrderMainStatus.ready.value
        self._increase_smnum(user.USid, clid, smnum, omnum, omstatus)
        ordermain = OrderMain.create({
            'OMid': omid,
            'OMno': self._generic_omno(),
            'USid': user.USid,
            'UCid': ucid,
            'OPayno': opayno,
            'OMmount': mount,
            'OMtrueMount': truemount,
            'OMstatus': omstatus,
            'OMrecvPhone': ua.UAtel,
            'OMrecvName': ua.UAname,
            'OMrecvAddress': omrecvaddress,
            'OMnum': omnum,
            'SMid': smid,
            'CLid': clid,
            'CLname': clname,
            'SMnum': smnum,
            'OMtype': OrderMainType.setmeal.value,
            'SMprice': trueunit
        })
        db.session.add(ordermain)
        return clname, truemount

    def _over_ordermain(self, omid):
        om = OrderMain.query.filter(
            OrderMain.OMid == omid, OrderMain.OMstatus == OrderMainStatus.ready.value,
            OrderMain.isdelete == 0).first()
        if not om:
            current_app.logger.error('完成订单有误，订单ID不存在')
            return
        # 完成订单
        with db.auto_commit():

            omtype = om.OMtype
            if int(omtype) == OrderMainType.product.value and int(om.PRtype) == ProductType.package.value:
                # 课时添加 - 积分商城
                omsmsum = int(om.SMnum) * int(om.OMnum)  # 订单总课时
                classes = json.loads(om.PRcontent)
                if not classes:
                    current_app.logger.error('课时信息录入异常 omid = {}'.format(omid))
                    return
                self._increase_uhnum(om.USid, classes.get('CLid'), omsmsum)

            if int(omtype) == OrderMainType.product.value and int(om.PRtype) == ProductType.coupon.value:
                # 优惠券变为可用
                CouponUser.query.filter(CouponUser.OMid == omid, CouponUser.isdelete == 0).update(
                    {'UCalreadyuse': CouponUserStatus.not_use.value}, synchronize_session=False)

            if int(omtype) == OrderMainType.setmeal.value:
                # 课时添加 - 课时套餐
                omsmsum = int(om.SMnum) * int(om.OMnum)
                self._increase_uhnum(om.USid, om.CLid, omsmsum)

        # 积分任务添加 todo 购物积分增加待确认
        current_app.logger.info('get omtype is {}'.format(omtype))
        if int(omtype) == OrderMainType.product.value:
            from .CConfig import CConfig
            CConfig()._judge_point(PointTaskType.buy_product.value, 1, om.USid)

    def _increase_uhnum(self, usid, clid, omsmsum):
        uh = UserHour.query.filter(
            UserHour.USid == usid, UserHour.CLid == clid, UserHour.isdelete == 0).first()
        if not uh:
            # 系统记录课时购买记录异常，创建新记录.课时直接到账
            uh = UserHour.create({
                'UHid': str(uuid.uuid1()),
                'USid': usid,
                'CLid': clid,
                'SMnum': omsmsum,
                'UHnum': omsmsum
            })

        else:
            uh.UHnum = int(uh.UHnum) + omsmsum
        db.session.add(uh)

    def test_over_ordermain(self):
        data = parameter_required()
        omid = data.get('omid')
        with db.auto_commit():
            om = OrderMain.query.filter(OrderMain.OMid == omid, OrderMain.isdelete == 0).first()
            current_app.logger.info('获取到订单 {}'.format(om))
            if om:
                om.update({'OMstatus': OrderMainStatus.ready.value})
            db.session.add(om)

        self._over_ordermain(omid)

        return Success('订单完结成功')

    @admin_required
    def send(self):
        data = parameter_required('omids')
        omids = data.get('omids')
        if not omids or not isinstance(omids, list):
            return Success('发货成功')
        with db.auto_commit():
            omlen = OrderMain.query.filter(
                OrderMain.OMid.in_(omids), OrderMain.isdelete == 0,
                OrderMain.OMstatus == OrderMainStatus.ready.value).update({
                'OMstatus': OrderMainStatus.send.value}, synchronize_session=False)
            current_app.logger.info('发货订单 {} 条， 修改成功 {} 条'.format(len(omids), omlen))

        return Success('发货成功')


