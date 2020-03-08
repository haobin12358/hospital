# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, DECIMAL, orm
from sqlalchemy.dialects.mysql import LONGTEXT

from hospital.common.base_model import Base, Column


class User(Base):
  	"""
    用户表
    """
    __tablename__ = "User"
    USid = Column(String(64), primary_key=True)
    USname = Column(String(255), nullable=False, comment='用户名')
    USalpha = Column(Text, url=True, comment='用户头像')
    USlevel = Column(Integer, default=0, comment='vip等级')
    UScount = Column(Integer, default=0, comment='用户账户')
    USintegral = Column(Integer, default=0, comment='用户积分')
    USopenid = Column(Text, comment='小程序 openid')
    USunionid = Column(Text, comment='统一unionID')

class Family(Base):
	"""
	我的家人
	"""
	FAid = Column(String(64), primary_key=True)
	USid = Column(String(64), comment='用户ID')
	FAtype = Column(Integer, default=0, comment='家人类型 0 孩子，1 父亲，2 母亲')
	FAname = Column(String(255), comment='家人姓名')
	FAage = Column(Integer, default=1, comment='家人年龄')
	FAidentification = Column(String(24), comment='身份证号')
	FAtel = Column(String(13), comment='手机号')
	FAgender = Column(Integer, default=0, comment='性别 {0： man，1：woman}')
	# AAid = Column(String(64), comment='区域ID')
	FAaddress = Column(Text)

