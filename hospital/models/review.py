"""
本文件用于评论数据表设置
create user: haobin12358
last update time:2020/4/2 1:18
"""

from sqlalchemy import Integer, String, Text, DECIMAL
from sqlalchemy.dialects.mysql import LONGTEXT
from hospital.extensions.base_model import Base, Column

class Review(Base):
    """
    评论
    """
    __tablename__ = "Review"
    RVid = Column(String(64), primary_key=True)
    USid = Column(String(64), comment="评价人id", nullable=False)
    USname = Column(String(255), comment="用户名")
    USavatar = Column(Text, url=True, comment='用户头像')
    RVcontent = Column(Text, comment="评论内容", nullable=False)
    DOid = Column(String(64), comment="医生id")
    RVtype = Column(Integer, nullable=False, comment="401课程， 402挂诊， 403活动， 404案例， 405视频")
    RVtypeid = Column(String(64), comment="关联id")
    RVnum = Column(DECIMAL(scale=2), default=5)

class ReviewPicture(Base):
    """
    评论关联图
    """
    __tablename__ = "ReviewPicture"
    RPid = Column(String(64), primary_key=True)
    RVid = Column(String(64), comment="评论id")
    RPpicture = Column(Text, url=True, comment="图片")