# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text, DateTime
from hospital.extensions.base_model import Base, Column


class Consultation(Base):
    """
    会诊
    """
    __tablename__ = 'Consultation'
    CONid = Column(String(64), primary_key=True)
    DOid = Column(String(64), comment='医生ID')
    CONstartTime = Column(DateTime, comment='会诊时间')
    CONendTime = Column(DateTime, comment='会诊时间')
    CONlimit = Column(Integer, default=-1, comment='限制人数')
    CONstatus = Column(Integer, default=0, comment='会诊状态')
    CONnote = Column(Text, comment='注意事项')
    DOname = Column(String(255), nullable=False, comment='医生名')
    DOtel = Column(String(13), default=0, comment='医生电话')
    DOtitle = Column(String(255), comment='医生职称')
    DOdetails = Column(Text, comment='医生简介')
    DOwxid = Column(String(255), comment='微信ID')
    DOskilledIn = Column(Text, comment='擅长方向')
    DEname = Column(String(255), comment='科室名')
    DEid = Column(String(64), comment='科室id')


class Enroll(Base):
    """
    报名
    """
    __tablename__ = 'Enroll'
    ENid = Column(String(64), primary_key=True)
    CONid = Column(String(64), comment='会诊ID')
    USid = Column(String(64), comment='用户id')
    USname = Column(String(255), comment='用户姓名')
    UStelphone = Column(String(13), comment='用户手机号')
