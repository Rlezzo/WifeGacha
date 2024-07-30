from .base import Base
from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

# 用户表
class User(Base):
    __tablename__ = 'users'
    # 属性
    id = Column(Integer, primary_key=True)  # 用户唯一标识
    # 定义与 子对象UserGroup 的关系
    user_groups = relationship('UserGroup', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)