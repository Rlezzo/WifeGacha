from .base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship

# 单用户角色事件表
class SingleUserCharacterEvent(Base):
    __tablename__ = 'single_user_character_events'
    # 属性
    id = Column(Integer, primary_key=True)  # 唯一标识
    user_group_id = Column(Integer, ForeignKey('user_groups.id', ondelete='CASCADE', name='fk_suce_ug_id'), nullable=False)  # 用户-群组ID，外键，级联删除
    character_id = Column(Integer, ForeignKey('characters.id', ondelete='CASCADE', name='fk_suce_character_id'), nullable=False)  # 角色ID，外键，级联删除
    event_type = Column(String, nullable=False)  # 事件类型
    result = Column(String, nullable=False)  # 事件结果
    event_time = Column(DateTime, nullable=False)  # 事件日期和时间

    # 关系
    user_group = relationship('UserGroup', back_populates='single_events_user_group')  # 关联到用户-群组
    character = relationship('Character', back_populates='single_events_character')  # 关联到角色
    
    # 索引
    __table_args__ = (
        Index('ix_suce_user_group_id', 'user_group_id'),  # 为 user_group_id 添加索引
        Index('ix_suce_character_id', 'character_id'),  # 为 character_id 添加索引
        Index('ix_suce_event_type', 'event_type'),  # 为 event_type 添加索引
        Index('ix_suce_result', 'result'),  # 为 result 添加索引
        Index('ix_suce_user_group_character', 'user_group_id', 'character_id'),  # 组合索引
        Index('ix_suce_character_event_type', 'character_id', 'event_type'),  # 组合索引
        Index('ix_suce_event_type_result', 'event_type', 'result'),  # 组合索引
        Index('ix_suce_user_group_event_type_result', 'user_group_id', 'event_type', 'result'),  # 组合索引
        Index('ix_suce_character_event_type_result', 'character_id', 'event_type', 'result')  # 组合索引
        )