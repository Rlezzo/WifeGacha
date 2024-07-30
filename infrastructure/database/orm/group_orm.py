from .base import Base
from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

# 群组表
class Group(Base):
    __tablename__ = 'groups'
    # 属性
    id = Column(Integer, primary_key=True)  # 群组唯一标识
    # 定义与 子对象UserGroup 的关系
    user_groups = relationship('UserGroup', back_populates='group', cascade='all, delete-orphan', passive_deletes=True)
    double_user_character_events = relationship('DoubleUserCharacterEvent', back_populates='group', cascade='all, delete-orphan', passive_deletes=True)