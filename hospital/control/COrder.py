# -*- coding: utf-8 -*-
import random
import re
import time
from datetime import datetime
from decimal import Decimal

from flask import current_app, request, json
import uuid

from hospital import JSONEncoder
from hospital.extensions.interface.user_interface import is_user, admin_required, token_required
from hospital.extensions.success_response import Success
from hospital.extensions.error_response import ParamsError, StatusError
from hospital.extensions.params_validates import parameter_required
from hospital.extensions.register_ext import db, wx_pay
from hospital.extensions.weixin.pay import WeixinPayError
from hospital.models import Admin, Coupon, Products, Classes, User, OrderMain, CouponUser, UserAddress, AddressProvince, \
    AddressCity, AddressArea, UserIntegral, OrderPay
from hospital.config.enums import ProductStatus, ProductType, AdminStatus, CouponUserStatus, OrderMainStatus, \
    OrderPayType


class COrder(object):
    @admin_required
    def list(self):
        pass

    @admin_required
    def get(self):
        pass

    @token_required
    def create(self):
        data = parameter_required()
        usid = getattr(request, 'user').id
        ucid = data.get('ucid')
        prid = data.get('prid')
        omnum = data.get('omnum')
        uaid = data.get('uaid')
        with db.auto_commit():
            product = Products.query.filter(Products.PRid == prid,
                                            Products.PRstatus == ProductStatus.usual.value).first_('商品已售空')
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
            omid = str(uuid.uuid1())
            opayno = wx_pay.nonce_str
            decimal_omnum = Decimal(omnum)
            mount = Decimal(product.PRprice if product.PRprice else 0) * decimal_omnum
            omintegral = int(product.PRintegral if product.PRintegral else 0) * omnum
            omintegralunit = product.PRvipIntegral if user.USlevel and product.PRvipIntegral else product.PRvipIntegral
            omintegralpayed = int(omintegralunit if omintegralunit else 0) * omnum
            if omintegralpayed:
                if omintegralpayed > int(user.USintegral):
                    raise ParamsError('用户积分不足')
                user.USintegral = int(user.USintegral) - omintegralpayed
                # 创建积分修改记录
                ui = UserIntegral.create({
                    'UIid': str(uuid.uuid1()),
                    'USid': usid,
                    'UIintegral': omintegralpayed,
                    'UIaction': 710,  # todo 修改为enum
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

            if uc:
                if uc.COdownline and Decimal(product.PRprice) >= Decimal(uc.COdownline):
                    # 优惠后价格
                    truemount = truemount - Decimal(uc.COsubtration)
                    if truemount < Decimal(0):
                        truemount = Decimal(0)
                    uc.UCalreadyuse = CouponUserStatus.had_use.value
                    db.session.add(uc)

                else:
                    raise ParamsError('商品价格达不到优惠券最低金额')
            content = ''
            if product.COid and product.PRtype == ProductType.coupon.value:
                # 优惠券商品 记录优惠券信息
                coupon = Coupon.query.filter(Coupon.COid == product.COid, Coupon.isdelete == 0).first_('商品已售空')
                content = json.dumps(coupon, cls=JSONEncoder)

            if product.CLid and product.PRtype == ProductType.package.value:
                classes = Classes.query.filter(Classes.CLid == product.CLid, Classes.isdelete == 0).first_('商品已售空')
                content = json.dumps(classes, cls=JSONEncoder)

            omstatus = OrderMainStatus.wait_pay.value
            if truemount == 0:
                omstatus = OrderMainStatus.ready.value

            # user.USintegral =
            product.PRstock -= omnum

            om = OrderMain.create({
                'OMid': omid,
                'OMno': self._generic_omno(),
                'USid': usid,
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
                'PRprice': product.PRprice,
                'PRvipPrice': product.PRvipPrice,
                'PRintegral': product.PRintegral,
                'PRvipIntegral': product.PRvipIntegral,
                'SMnum': product.SMnum,
                'PRtitle': product.PRtitle,
                'PRmedia': product.PRmedia,
                'PRcontent': content,
                'OMnum': omnum,
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
        from ..extensions.tasks import auto_cancle_order
        auto_cancle_order.apply_async(args=(omid,), countdown=30 * 60, expires=40 * 60, )
        # # 生成支付信息
        body = product.PRtitle
        openid = user.USopenid
        if not truemount:
            pay_type = OrderPayType.integral.value
            pay_args = 'integralpay'
        elif not omintegralpayed:
            pay_args = self._pay_detail(opayno, float(truemount), body, openid=openid)
            pay_type = OrderPayType.wx.value
        else:
            pay_args = self._pay_detail(opayno, float(truemount), body, openid=openid)
            pay_type = OrderPayType.mix.value

        response = {
            'paytype': pay_type,
            'args': pay_args
        }
        return Success('下单成功', data=response)

    def pay(self):
        """订单发起支付"""
        data = parameter_required('omid')
        omid = data.get('omid')

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
            # 商品库存
            product = Products.query.filter(Products.PRid == ordermain.PRid, Products.isdelete == 0).first()
            if product:
                product.PRstock += int(ordermain.OMnum)

            if product.PRtype == ProductType.package.value:
                # 收回课时






    def wechat_notify(self):
        """微信支付回调"""
        pass

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
