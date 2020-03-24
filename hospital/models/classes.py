# -*- coding: utf-8 -*-
"""
本文件用于处理课程及课程预约相关数据库结构
create user: haobin12358
last update time:2020/3/19 22:23
"""
import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, DECIMAL, orm, DATE, Float
from sqlalchemy.dialects.mysql import LONGTEXT

from hospital.extensions.base_model import Base, Column

class Classes(Base):
    """
    课程
    """
    __tablename__ = "Classes"
    CLid = Column(String(64), primary_key=True)
    CLname = Column(String(128), nullable=False, comment="课程名称")
    CLpicture = Column(Text, url=True, comment="课程图")
    DEid = Column(String(64), comment="科室id")
    DEname = Column(String(255), nullable=False, comment="科室名称")
    CLintroduction = Column(Text, comment="详细介绍")
    CLindex = Column(Integer, default=1, comment="权重")
    CLprice = Column(Float, comment="课时价格")

class Course(Base):
    """
    课程排班
    """
    __tablename__ = "Course"
    COid = Column(String(64), primary_key=True)
    CLid = Column(String(64), comment="课程id")
    CLname = Column(String(128), comment="课程名称")
    DOid = Column(String(64), comment="医生id")
    DOname = Column(String(255), comment="医生名称")
    COstarttime = Column(DateTime, nullable=False, comment="开始时间")
    COendtime = Column(DateTime, nullable=False, comment="结束时间")
    COnum = Column(Integer, default=0, comment="限制人数")
    COstatus = Column(Integer, default=101, comment="课程状态 {101: 未开始 102: 已开始 103：已结束}")

class Subscribe(Base):
    """
    课程预约
    """
    __tablename__ = "Subscribe"
    SUid = Column(String(64), primary_key=True)
    COid = Column(String(64), comment="排班id")
    CLname = Column(String(128), comment="课程名称")
    COstarttime = Column(DateTime, comment="课程开始时间，即预约课程时间")
    DOname = Column(String(255), comment="医生名称")
    USname = Column(String(255), comment="用户名")
    USid = Column(String(64), comment="用户id")
    UStelphone = Column(String(16), comment="用户手机号")
    SUstatus = Column(Integer, default=201, comment="预约状态{201：已预约，202：已上课，203：已评价}")

class Setmeal(Base):
    """
    课程套餐
    """
    __tablename__ = "Setmeal"
    SMid = Column(String(64), primary_key=True)
    CLid = Column(String(64), comment="课程id")
    CLname = Column(String(128), comment="课程名称")
    SMnum = Column(Integer, nullable=False, comment="课时数")
    SMprice = Column(Float, nullable=False, comment="套餐价格")