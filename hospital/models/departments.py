# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text, DateTime, orm
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
        self.fields = ['DEid', 'DEname', 'createtime']


class Symptom(Base):
    """症状"""
    __tablename__ = 'Symptom'
    SYid = Column(String(64), primary_key=True)
    SYname = Column(String(255), nullable=False, comment='症状名')
    SYsort = Column(Integer, default=0, comment='症状排序')
    DEid = Column(String(64), comment='科室id')

    @orm.reconstructor
    def __init__(self):
        super(Symptom, self).__init__()
        self.fields = ['SYid', 'SYname']


class Doctor(Base):
    """医生"""
    __tablename__ = 'Doctor'
    DOid = Column(String(64), primary_key=True)
    DOname = Column(String(255), nullable=False, comment='医生名')
    DOtel = Column(String(13), default=0, comment='医生电话')
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
        self.fields = ['DEid', 'DOname', 'DOid', 'DOtitle', 'createtime']


class DoctorMedia(Base):
    """医生图片"""
    __tablename__ = 'DoctorMedia'
    DMid = Column(String(64), primary_key=True)
    DOid = Column(String(64), comment='医生ID')
    DMtype = Column(Integer, default=0, comment='0 医生主图 1 医生列表图 2 医生二维码')
    DMmedia = Column(Text, url=True, comment='图片链接')
    DMsort = Column(Integer, default=0, comment='图片顺序')


class Example(Base):
    """案例"""
    __tablename__ = 'Example'
    EXid = Column(String(64), primary_key=True)
    SYid = Column(String(64), comment='症状ID')
    EXname = Column(String(255), comment='患者姓名')
    EXgender = Column(Integer, default=0, comment='性别 {0： man，1：woman}')
    EXage = Column(String(8), comment='年龄')
    EXheight = Column(String(8), comment='身高')
    EXweight = Column(String(8), comment='体重')
    EXaddr = Column(String(256), comment='来历')
    EXtreated = Column(DateTime, comment='就诊时间')
    EXchiefComplaint = Column(Text, comment='主诉')
    EXclinicVisitHistory = Column(Text, comment='就诊史')
    EXcaseAnalysis = Column(Text, comment='案例分析')
    EXinspectionResults = Column(Text, comment='校验结果')
    EXdiagnosis = Column(Text, comment='诊断')
    EXtreatmentPrinciple = Column(Text, comment='治疗原则')
    EXtreatmentOutcome = Column(Text, comment='治疗结果')
    EXperoration = Column(Text, comment='结束语')
    EXbriefIntroduction = Column(Text, comment='简介')
    EXalpha = Column(Text, comment='主图')
    EXsort = Column(Integer, default=0, comment='排序')

    @orm.reconstructor
    def __init__(self):
        super(Example, self).__init__()
        self.fields = ['EXid', 'EXname', 'SYid', 'createtime', 'EXalpha']
