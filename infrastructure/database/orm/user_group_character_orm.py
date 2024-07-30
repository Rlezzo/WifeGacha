from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class UserGroupCharacter(Base):
    __tablename__ = 'user_group_characters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_group_id = Column(Integer, ForeignKey('user_groups.id', ondelete='CASCADE', name='fk_ugc_ug_id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id', ondelete='CASCADE', name='fk_ugc_character_id'), nullable=False)
    acquisition_time = Column(DateTime, nullable=False)  # 第一次添加这个条目的时间
    
    user_group = relationship('UserGroup', back_populates='user_group_characters')
    character = relationship('Character', back_populates='user_group_characters')
    stats = relationship('UserGroupCharacterStats', back_populates='user_group_character', cascade='all, delete-orphan', uselist=False, passive_deletes=True)  # 关联到统计表，一对一，用数据库自身的级联删除
    
    __table_args__ = (
        UniqueConstraint('user_group_id', 'character_id', name='_user_group_character_uc'),
        Index('ix_user_group_characters_user_group_id', 'user_group_id'),
        Index('ix_user_group_characters_character_id', 'character_id'),
        Index('ix_user_group_characters_user_group_character', 'user_group_id', 'character_id')
    )