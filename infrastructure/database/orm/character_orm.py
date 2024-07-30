from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class Character(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)  # 添加唯一约束
    pool_name = Column(String, nullable=False)
    image_name = Column(String, nullable=False, unique=True)  # 添加唯一约束
    image_path = Column(String, nullable=False)
    
    user_group_characters = relationship('UserGroupCharacter', back_populates='character', cascade='all, delete-orphan', passive_deletes=True)
    current_ug_characters = relationship('CurrentUserGroupCharacter', back_populates='character', cascade='all, delete-orphan', passive_deletes=True)
    single_events_character = relationship('SingleUserCharacterEvent', back_populates='character', cascade='all, delete-orphan', passive_deletes=True)
    double_events_initiator_character =  relationship('DoubleUserCharacterEvent', foreign_keys='DoubleUserCharacterEvent.initiator_current_character_id', back_populates='initiator_character', cascade='all, delete-orphan', passive_deletes=True)
    double_events_receiver_character = relationship('DoubleUserCharacterEvent', foreign_keys='DoubleUserCharacterEvent.receiver_current_character_id', back_populates='receiver_character', cascade='all, delete-orphan', passive_deletes=True)
   
    __table_args__ = (
        UniqueConstraint('name', name='_character_name_uc'),
        UniqueConstraint('image_name', name='_character_image_name_uc'),
    )