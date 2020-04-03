# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text, DateTime, DECIMAL, orm
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
    CONlimit = Column(Integer, default=-1 ,comment='限制人数')
    CONstatus = Column(Integer, default=0, comment='会诊状态')
