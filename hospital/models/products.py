# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text, DECIMAL, orm, Boolean, DateTime
from hospital.extensions.base_model import Base, Column


class Products(Base):
    """
    商品
    """
    ____tablename__ = 'Products'
    PRid = Column(String(64), primary_key=True)
    PRtitle = Column(String(255), comment='商品名')
    PRtype = Column(Integer, default=0, comment='商品类型')
    PRmedia = Column(Text, url=True, comment='商品主图')
    PRstatus = Column(Integer, default=0, comment='商品状态')
    PRprice = Column(DECIMAL(scale=2), comment='商品价格')
    PRvipPrice = Column(DECIMAL(scale=2), comment='VIP价格')
    PRintegral = Column(Integer, comment='积分价格')
    PRvipIntegral = Column(Integer, comment='vip积分价格')
    PRstock = Column(Integer, comment='库存')
    COid = Column(String(64), comment='优惠券ID')
    PRdetails = Column(Text, url_list=True, comment='商品详情图')
    PRdesc = Column(Text, comment='兑换描述')
    PRsort = Column(Integer, default=0, comment='排序')
    CLid = Column(String(64), comment='课程ID')
    SMnum = Column(Integer, default=0, comment='课时数')

    @orm.reconstructor
    def __init__(self):
        super(Products, self).__init__()
        self.hide('PRdesc', 'PRdetails')


class OrderMain(Base):
    """
    订单
    """
    __tablename__ = 'OrderMain'
    OMid = Column(String(64), primary_key=True)
    OMno = Column(String(64), nullable=False, comment='订单编号')
    USid = Column(String(64), nullable=False, comment='用户id')
    # UseCoupon = Column(Boolean, default=False, comment='是否优惠券')
    OPayno = Column(String(64), comment='付款流水号,与orderpay对应')
    OMmount = Column(DECIMAL(precision=28, scale=2), nullable=False, comment='总价')
    OMtrueMount = Column(DECIMAL(precision=28, scale=2), nullable=False, comment='实际总价')
    OMstatus = Column(Integer, default=0, comment='订单状态 0待付款 30完成 -40取消交易')
    OMrecvPhone = Column(String(11), nullable=False, comment='收货电话')
    OMrecvName = Column(String(11), nullable=False, comment='收货人姓名')
    OMrecvAddress = Column(Text, nullable=False, comment='地址')
    OMintegralpayed = Column(Integer, comment='组合支付时，实际支付的积分')
    OMintegral = Column(Integer, comment='组合支付时积分数')
    UCid = Column(String(64), comment='优惠券ID')
    OMnum = Column(Integer, default=1, comment='数量')
    OMtype = Column(Integer, default=0, comment='订单类型 0 积分商城商品订单 2 课时套餐订单')

    # 课时套餐 数据记录
    SMid = Column(String(64), comment='课时套餐ID')
    CLid = Column(String(64), comment="课程id")
    CLname = Column(String(128), comment="课程名称")
    SMnum = Column(Integer, comment="课时数")
    SMprice = Column(DECIMAL(scale=2), comment="套餐价格")

    PRid = Column(String(64), comment='商品id')
    PRprice = Column(DECIMAL(precision=28, scale=2), comment='单价')
    PRintegral = Column(Integer, comment='积分价格')
    PRtitle = Column(String(255), comment='商品标题')
    PRmedia = Column(String(255), comment='主图', url=True)
    PRcontent = Column(Text, comment='关联优惠券/课程的信息')
    PRtype = Column(Integer, default=0, comment='商品类型')

    @orm.reconstructor
    def __init__(self):
        super(OrderMain, self).__init__()
        self.add('createtime')
        self.hide('PRcontent', 'USid')



class OrderPay(Base):
    """
    付款流水
    """
    __tablename__ = 'OrderPay'
    OPayid = Column(String(64), primary_key=True)
    OPayno = Column(String(64), index=True, comment='交易号, 自己生成')  # 即out_trade_no
    OPayType = Column(Integer, default=0, comment='支付方式 0 微信 10 积分')
    OPaytime = Column(DateTime, comment='付款时间')
    OPayMount = Column(DECIMAL(precision=28, scale=2), comment='付款金额')
    OPaysn = Column(String(64), comment='第三方支付流水')
    OPayJson = Column(Text, comment='回调原文')
    OPaymarks = Column(String(255), comment='备注')

