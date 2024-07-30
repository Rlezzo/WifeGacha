from dataclasses import dataclass
import datetime
from typing import Optional

@dataclass
class UserGroupCharacter:
    id: int
    user_group_id: int
    character_id: int
    acquisition_time: datetime  # 获取时间，使用 datetime 类型存储时间戳
    stats: Optional['UserGroupCharacterStats'] = None  # 关系字段，默认为 None