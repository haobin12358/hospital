# -*- coding: utf-8 -*-
"""
用户相关信息：家人，地址等
create user: wiilz
last update time:2020/3/15 22:22
"""
from sqlalchemy import Integer, String, Text, Boolean
from hospital.extensions.base_model import Base, Column


class User(Base):
    """用户"""
    __tablename__ = "User"
    USid = Column(String(64), primary_key=True)
    USname = Column(String(255), nullable=False, comment='用户名')
    USavatar = Column(Text, url=True, comment='用户头像')
    USlevel = Column(Integer, default=0, comment='vip等级')
    USintegral = Column(Integer, default=0, comment='用户积分')
    USopenid = Column(Text, comment='小程序 openid')
    USunionid = Column(Text, comment='统一 unionID')


class Family(Base):
    """家人"""
    __tablename__ = "Family"
    FAid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户ID')
    FAtype = Column(Integer, default=0, comment='家人类型 0 孩子，1 父亲，2 母亲')
    FAname = Column(String(255), comment='家人姓名')
    FAage = Column(Integer, default=1, comment='家人年龄')
    FAidentification = Column(String(18), comment='身份证号')
    FAtel = Column(String(13), comment='手机号')
    FAgender = Column(Integer, default=0, comment='性别 {0： man，1：woman}')
    AAid = Column(String(64), comment='居住地区域ID')
    FAaddress = Column(Text, comment='家人居住地')


class UserAddress(Base):
    """用户地址"""
    __tablename__ = 'UserAddress'
    UAid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户id')
    UAname = Column(String(16), nullable=False, comment='收货人姓名')
    UAtel = Column(String(16), nullable=False, comment='收货人电话')
    UAtext = Column(String(255), nullable=False, comment='具体地址')
    UAdefault = Column(Boolean, default=False, comment='默认收货地址')
    AAid = Column(String(8), nullable=False, comment='关联的区域id')
    # UApostalcode = Column(String(8), comment='邮政编码')
