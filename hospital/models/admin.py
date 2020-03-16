"""
本文件用于记录后台管理员及管理员操作行为
create user: haobin12358
last update time:2020/3/12 19:39
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from hospital.extensions.base_model import Base, Column

class Admin(Base):
    """
    管理员
    """
    __tablename__ = 'Admin'
    ADid = Column(String(64), primary_key=True)
    ADname = Column(String(255), comment='管理员名')
    ADtelphone = Column(String(13), comment='管理员联系电话')
    ADpassword = Column(Text, nullable=False, comment='密码')
    ADheader = Column(Text, comment='头像', url=True)
    ADlevel = Column(Integer, default=2, comment='管理员等级，{1: 超级管理员, 2: 普通管理员')
    ADstatus = Column(Integer, default=0, comment='账号状态，{0:正常, 1: 被冻结, 2: 已删除}')


class AdminActions(Base):
    """
    记录管理员行为
    """
    __tablename__ = 'AdminAction'
    AAid = Column(String(64), primary_key=True)
    ADid = Column(String(64), comment='管理员id')
    ADtype = Column(String(64), comment='管理员类型, {1:超级管理员 2:管理员 3：医生}')
    AAaction = Column(Integer, default=1, comment='管理员行为, {1: 添加, 2: 删除 3: 修改 4:登录}')
    AAmodel = Column(String(255), comment='操作的数据表')
    AAdetail = Column(LONGTEXT, default='none', comment='请求的data')
    AAkey = Column(String(255), comment='操作数据表的主键的值')