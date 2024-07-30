from dataclasses import dataclass
from typing import Optional, List

@dataclass
class UserGroup:
    id: int
    user_id: int
    group_id: int
    user_group_characters: Optional[List['UserGroupCharacter']] = None
    current_ug_characters: Optional['CurrentUserGroupCharacter'] = None
    single_events_user_group: Optional[List['SingleUserCharacterEvent']] = None
    double_events_initiator_ug: Optional[List['DoubleUserCharacterEvent']] = None
    double_events_receiver_ug: Optional[List['DoubleUserCharacterEvent']] = None
    