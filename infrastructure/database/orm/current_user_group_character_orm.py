from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class CurrentUserGroupCharacter(Base):
    __tablename__ = 'current_user_group_character'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_group_id = Column(Integer, ForeignKey('user_groups.id', ondelete='CASCADE', name='fk_cugc_ug_id'), nullable=False, unique=True)
    character_id = Column(Integer, ForeignKey('characters.id', ondelete='CASCADE', name='fk_cugc_cid'))
    update_time = Column(DateTime, nullable=False)

    user_group = relationship('UserGroup', back_populates='current_ug_characters')
    character = relationship('Character', back_populates='current_ug_characters')