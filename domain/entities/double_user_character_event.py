from dataclasses import dataclass
import datetime
from typing import Optional

@dataclass
class DoubleUserCharacterEvent:
    id: int
    group_id: int
    action_initiator_user_group_id: int
    action_receiver_user_group_id: int
    event_type: str
    event_time: datetime  # 使用 datetime 类型存储时间戳
    initiator_current_character_id: Optional[int] = None
    receiver_current_character_id: Optional[int] = None
    result: Optional[str] = None
