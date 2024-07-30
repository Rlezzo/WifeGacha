from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CurrentUserGroupCharacter:
    id: int
    user_group_id: int
    character_id: int
    update_time: datetime

    # 由于关系字段在业务逻辑中可能不常用，可以选择不在数据类中定义这些关系字段
    user_group: Optional['UserGroup'] = None
    character: Optional['Character'] = None