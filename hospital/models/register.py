# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, Text, Date, DECIMAL
from hospital.extensions.base_model import Base, Column


class Register(Base):
    """
    挂号
    """
    __tablename__ = 'Register'
    REid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment='用户ID')
    FAid = Column(String(64), comment='就诊人ID')
    DEid = Column(String(64), comment='科室ID')
    REdate = Column(Date, comment='就诊时间')
    REamOrPm = Column(Integer, default=0, comment='上午或下午 {0:上午, 1:下午}')
    REremarks = Column(Text, comment='特别注意')
    REstatus = Column(Integer, default=0, comment='挂号状态 {0:排队中, 1:待就诊, -1： 未就诊'
                                                  '2: 预约日号已满协调到新日期(同样是待就诊), 3: 待评价, 4: 已评价}')
    REtansferDate = Column(Date, comment='如果被调剂了挂号日期，则需要返回该字段')
    REtansferAmOrPm = Column(Integer, comment='如果被调剂了挂号日期，则需要返回该字段')
    REfee = Column(DECIMAL(scale=2), comment='费用')
    REcode = Column(String(64), comment='排队号')
    DOtel = Column(String(13), comment='医生手机号')
    DOname = Column(String(255), comment='医生名')
    DOmedia = Column(Text, comment='医生图片')
    DOtitle = Column(String(255), comment='职称')
    DOid = Column(String(64), comment='医生ID')
