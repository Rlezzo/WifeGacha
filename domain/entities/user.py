from dataclasses import dataclass
from typing import Optional, List

@dataclass
class User:
    id: int
    user_groups: Optional[List['UserGroup']] = None  # 关系字段，默认为 None