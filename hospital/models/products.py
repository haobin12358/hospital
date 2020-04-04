# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text, DateTime, DECIMAL, orm
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

    @orm.reconstructor
    def __init__(self):
        super(Products, self).__init__()
        self.hide('PRdesc', 'PRdetails')
