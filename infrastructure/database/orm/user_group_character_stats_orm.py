from sqlalchemy import Column, Index, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class UserGroupCharacterStats(Base):
    __tablename__ = 'user_group_character_stats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_group_character_id = Column(Integer, ForeignKey('user_group_characters.id', ondelete='CASCADE', name='fk_ugcs_ugc_id'), nullable=False)
    user_group_id = Column(Integer, ForeignKey('user_groups.id', ondelete='CASCADE', name='fk_ugcs_ug_id'), nullable=False)
    character_id = Column(Integer, ForeignKey('characters.id', ondelete='CASCADE', name='fk_ugcs_character_id'), nullable=False)
    
    lastest_acquisition_time = Column(DateTime, nullable=False) # 最后一次抽到的时间
    draw_count = Column(Integer)
    acquired_by_ex_count = Column(Integer)
    acquired_by_ntr_count = Column(Integer)
    
    mating_count = Column(Integer)
    divorce_count = Column(Integer)
    # 其他统计数据字段

    user_group_character = relationship('UserGroupCharacter', back_populates='stats')
    user_group = relationship('UserGroup', back_populates='user_group_character_stats')
    
    __table_args__ = (
        UniqueConstraint('user_group_character_id', name='_user_group_character_stats_uc'),
        Index('ix_user_group_character_stats_user_group_id', 'user_group_id'),
        Index('ix_user_group_character_stats_character_id_user_group_id', 'character_id', 'user_group_id')
    )