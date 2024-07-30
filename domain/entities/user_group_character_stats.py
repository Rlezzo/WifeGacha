from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserGroupCharacterStats:
    id: int
    user_group_character_id: int
    user_group_id: int
    character_id: int
    lastest_acquisition_time: datetime #最后获取时间，因为获取必修改draw_count，所以放stats里
    draw_count: int
    acquired_by_ex_count: int
    acquired_by_ntr_count: int
    # 其他统计数据字段
    mating_count: int
    divorce_count: int