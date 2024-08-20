from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from domain.entities import SingleEvent

class SingleUserCharacterEventRepository(ABC):
    @abstractmethod
    async def add(self, single_domain: SingleEvent) -> None:
        pass
    
    @abstractmethod
    async def get_most_frequent_character_in_group(
        self,
        group_id: int,
        event_type: Optional[str] = None,
        result: Optional[str] = None
        ) -> Tuple[Optional[int], int]:
        pass
    
    @abstractmethod
    async def get_most_frequent_user_in_group(
        self,
        group_id: int,
        event_type: Optional[str] = None,
        result: Optional[str] = None
    ) -> Tuple[Optional[int], int]:
        pass

    @abstractmethod
    async def get_event_count_by_user_group_id(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None
    ) -> int:
        pass

    @abstractmethod
    async def get_character_id_by_user_group_id(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
    ) -> List[int]:
        pass
