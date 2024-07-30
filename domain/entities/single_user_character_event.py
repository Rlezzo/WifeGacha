from dataclasses import dataclass
import datetime
from typing import Optional

@dataclass
class SingleUserCharacterEvent:
    id: int
    user_group_id: int
    character_id: int
    event_type: str
    event_time: datetime  # 使用 datetime 类型存储时间戳
    result: Optional[str] = None