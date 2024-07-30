from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
from domain.entities import Stats, UserGroup, Character, ActionType, AcqMethod

class UserGroupCharacterStatsRepository(ABC):
    @abstractmethod
    async def add(self, stats_domain: Stats) -> None:
        pass

    @abstractmethod
    async def update_acquired_count(self, stats_domain: Stats) -> None:
        pass
    
    @abstractmethod
    async def update_action_count(self, stats_domain: Stats) -> None:
        pass
    
    @abstractmethod
    async def get_by_user_group_character(self, user_group: UserGroup, character: Character) -> Optional[Stats]:
        pass
    
    @abstractmethod
    async def get_top_action_count_character_in_group(self, group_id: int, action: ActionType) -> Tuple[Optional[int], int]:
        pass
    
    @abstractmethod
    async def get_total_count_in_group(
        self, 
        group_id: int, 
        count_type: Union[AcqMethod, ActionType],
        character_id: Optional[int] = None
    ) -> int:
        pass
    
    @abstractmethod
    async def get_total_count_by_user_group_id(
        self, 
        user_group_id: int, 
        count_type: Union[AcqMethod, ActionType],
        character_id: Optional[int] = None
    ) -> int:
        pass