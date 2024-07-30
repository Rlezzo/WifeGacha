from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Character:
    id: int
    name: str
    pool_name: str
    image_name: str
    image_path: str
    user_group_characters: Optional[List['UserGroupCharacter']] = None  # 关系字段，默认为 None
    current_ug_characters: Optional[List['CurrentUserGroupCharacter']] = None
    single_events_character: Optional[List['SingleUserCharacterEvent']] = None  # 关系字段，默认为 None
    double_events_initiator_character: Optional[List['DoubleUserCharacterEvent']] = None  # 关系字段，默认为 None
    double_events_receiver_character: Optional[List['DoubleUserCharacterEvent']] = None  # 关系字段，默认为 None
