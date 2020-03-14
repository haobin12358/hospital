# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, DECIMAL, orm
from sqlalchemy.dialects.mysql import LONGTEXT

from hospital.extensions.base_model import Base, Column


class Departments(Base):
    """科室"""
    __tablename__ = 'Departments'
    DEid = Column(String(64), primary_key=True)
    DEname = Column(String(255), nullable=False, comment='科室名')
    DEalpha = Column(Text, url=True, comment='科室主图')
    DEsort = Column(Integer, default=0, comment='科室排序')
    DEintroduction = Column(Text, comment='科室介绍')
    DEicon = Column(Text, url=True, comment='科室icon')
    DEicon2 = Column(Text, url=True, comment='科室icon2')

    @orm.reconstructor
    def __init__(self):
        super(Departments, self).__init__()
        self.fields = ['DEid', 'DEname']


class Symptom(Base):
    """症状"""

    __tablename__ = 'Symptom'
    SYid = Column(String(64), primary_key=True)
    SYname = Column(String(255), nullable=False, comment='症状名')
    SYsort = Column(Integer, default=0, comment='症状排序')
    DEid = Column(String(64), comment='科室id')


class Doctor(Base):
    """医生"""
    __tablename__ = 'Doctor'
    DOid = Column(String(64), primary_key=True)
    DOname = Column(String(255), nullable=False, comment='医生名')
    DOtel = Column(Integer, default=0, comment='医生电话')
    DOtitle = Column(String(255), comment='医生职称')
    DOdetails = Column(Text, comment='医生简介')
    DOwxid = Column(String(255), comment='微信ID')
    DOskilledIn = Column(Text, comment='擅长方向')
    DOsort = Column(Integer, default=0, comment='科室医生排序')
    DOpassword = Column(String(255), comment='医生登录密码')
    # DOshift = Column(DateTime, comment='会诊时间')
    DEid = Column(String(64), comment='科室id')

    @orm.reconstructor
    def __init__(self):
        super(Doctor, self).__init__()
        self.fields = ['DEid', 'DOname', 'DOid', 'DOtitle']


class DoctorMedia(Base):
    """医生图片"""
    __tablename__ = 'DoctorMedia'
    DMid = Column(String(64), primary_key=True)
    DOid = Column(String(64), comment='医生ID')
    DMtype = Column(Integer, default=0, comment='0 医生主图 1 医生列表图 2 医生二维码')
    DMmedia = Column(Text, comment='图片链接')
    DMsort = Column(Integer, default=0, comment='图片顺序')
