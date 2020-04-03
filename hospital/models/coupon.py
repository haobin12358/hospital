# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, DECIMAL, orm
from sqlalchemy.dialects.mysql import LONGTEXT

from hospital.extensions.base_model import Base, Column

class Coupon(Base):
    """优惠券"""
    __tablename__ = 'Coupon'
    COid = Column(String(64), primary_key=True)
    COstatus = Column(Integer, default=501, comment='状态501可领取502已结束')
    COstarttime = Column(DateTime, comment='有效起始时间')
    COendtime = Column(DateTime, comment='有效期结束时间')
    COdownline = Column(DECIMAL(scale=2), comment='使用最低金额限制,0 为无限制')
    COsubtration = Column(DECIMAL(scale=2), default=0, comment='优惠价格')
    COlimitnum = Column(Integer, default=0, comment='发放数量')
    COgetnum = Column(Integer, default=0, comment='已领数量')

class CouponUser(Base):
    """用户的优惠券"""
    __tablename__ = 'CouponUser'
    UCid = Column(String(64), primary_key=True)
    COid = Column(String(64), nullable=False, comment='优惠券id')
    USid = Column(String(64), nullable=False, comment='用户id')
    COsubtration = Column(DECIMAL(scale=2), default=0, comment='优惠价格')
    COstarttime = Column(DateTime, comment='有效起始时间')
    COendtime = Column(DateTime, comment='有效期结束时间')
    COdownline = Column(DECIMAL(scale=2), comment='使用最低金额限制,0 为无限制')
    UCalreadyuse = Column(Integer, default=602, comment='是否已经使用 601已使用602未使用603已过期')