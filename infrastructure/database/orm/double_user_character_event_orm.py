from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class DoubleUserCharacterEvent(Base):
    __tablename__ = 'double_user_character_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    action_initiator_user_group_id = Column(Integer, ForeignKey('user_groups.id', ondelete='CASCADE', name='fk_duce_init_ug_id'), nullable=False)
    action_receiver_user_group_id = Column(Integer, ForeignKey('user_groups.id', ondelete='CASCADE', name='fk_duce_rece_ug_id'), nullable=False)
    initiator_current_character_id = Column(Integer, ForeignKey('characters.id', ondelete='CASCADE', name='fk_duce_init_cid'))
    receiver_current_character_id = Column(Integer, ForeignKey('characters.id', ondelete='CASCADE', name='fk_duce_rece_cid'))
    event_type = Column(String, nullable=False)
    result = Column(String, nullable=True)
    event_time = Column(DateTime, nullable=False)

    group = relationship('Group', back_populates='double_user_character_events')
    initiator_user = relationship('UserGroup', foreign_keys=[action_initiator_user_group_id], back_populates='double_events_initiator_ug')
    receiver_user = relationship('UserGroup', foreign_keys=[action_receiver_user_group_id], back_populates='double_events_receiver_ug')
    initiator_character = relationship('Character', foreign_keys=[initiator_current_character_id], back_populates='double_events_initiator_character')
    receiver_character = relationship('Character', foreign_keys=[receiver_current_character_id], back_populates='double_events_receiver_character')

    __table_args__ = (
        Index('ix_double_user_character_events_group_id', 'group_id'),
        Index('ix_double_user_character_events_action_initiator_user_group_id', 'action_initiator_user_group_id'),
        Index('ix_double_user_character_events_action_receiver_user_group_id', 'action_receiver_user_group_id'),
        Index('ix_double_user_character_events_initiator_current_character_id', 'initiator_current_character_id'),
        Index('ix_double_user_character_events_receiver_current_character_id', 'receiver_current_character_id'),
        Index('ix_double_user_character_events_event_type', 'event_type'),
        Index('ix_double_user_character_events_result', 'result'),
        Index('ix_double_user_character_events_event_type_result', 'event_type', 'result'),  # 组合索引
        Index('ix_double_user_character_events_initiator_receiver', 'action_initiator_user_group_id', 'action_receiver_user_group_id'),  # 组合索引
        Index('ix_double_user_character_events_initiator_event_type', 'action_initiator_user_group_id', 'event_type'),  # 组合索引
        Index('ix_double_user_character_events_receiver_event_type', 'action_receiver_user_group_id', 'event_type'),  # 组合索引
        Index('ix_double_user_character_events_character_event_type', 'initiator_current_character_id', 'event_type', 'result'),  # 组合索引
        Index('ix_double_user_character_events_character_event_type_result', 'receiver_current_character_id', 'event_type', 'result')  # 组合索引
    )