from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Group:
    id: int
    user_groups: Optional[List['UserGroup']] = None  # 关系字段，默认为 None
    double_user_character_events: Optional[List['DoubleUserCharacterEvent']] = None  # 关系字段，默认为 None