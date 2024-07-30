from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .base import Base

class UserGroup(Base):
    __tablename__ = 'user_groups'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增主键
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE', name='fk_ug_user_id'), nullable=False) # 用户ID，外键，级联删除
    group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE', name='fk_ug_group_id'), nullable=False) # 群ID，外键，级联删除
    
    user = relationship('User', back_populates='user_groups') # 关联到用户
    group = relationship('Group', back_populates='user_groups') # 关联到群
    user_group_characters = relationship('UserGroupCharacter', back_populates='user_group', cascade='all, delete-orphan', passive_deletes=True)
    user_group_character_stats = relationship('UserGroupCharacterStats', back_populates='user_group', cascade='all, delete-orphan', passive_deletes=True)
    current_ug_characters = relationship('CurrentUserGroupCharacter', back_populates='user_group', cascade='all, delete-orphan', passive_deletes=True)
    single_events_user_group = relationship('SingleUserCharacterEvent', back_populates='user_group', cascade='all, delete-orphan', passive_deletes=True)
    double_events_initiator_ug = relationship('DoubleUserCharacterEvent', foreign_keys='DoubleUserCharacterEvent.action_initiator_user_group_id', back_populates='initiator_user', cascade='all, delete-orphan', passive_deletes=True)
    double_events_receiver_ug = relationship('DoubleUserCharacterEvent', foreign_keys='DoubleUserCharacterEvent.action_receiver_user_group_id', back_populates='receiver_user', cascade='all, delete-orphan', passive_deletes=True)
        
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='_user_group_uc'), # 联合唯一约束，确保每个用户在每个群组中只能有一个记录
        Index('ix_user_groups_user_id', 'user_id'), # 为 user_id 添加索引
        Index('ix_user_groups_group_id', 'group_id'), # 为 group_id 添加索引
        Index('ix_user_groups_user_group', 'user_id', 'group_id') # 为 user_id 和 group_id 添加复合索引
    )