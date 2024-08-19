from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from domain.entities import DoubleEvent

class DoubleUserCharacterEventRepository(ABC):
    @abstractmethod
    async def add(self, double_domain: DoubleEvent) -> None:
        pass
    
    @abstractmethod
    async def get_most_frequent_character_in_group(
        self, 
        group_id: int, 
        event_type: Optional[str] = None, 
        result: Optional[str] = None, 
        receiver: bool = True
        ) -> Tuple[Optional[int], int]:
        pass
    
    @abstractmethod
    async def get_most_frequent_user(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
        is_initiator: bool = True
    ) -> Tuple[Optional[int], int]:
        pass
            
    @abstractmethod
    async def get_event_count_in_group(
        self,
        group_id: int,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None,
        receiver: bool = True
    ) -> int:
        pass
    
    @abstractmethod
    async def get_event_count_by_user_group_id(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None,
        is_user_receiver: bool = False,
        is_character_receiver: bool = True
    ) -> int:
        pass

    @abstractmethod
    async def get_current_receiver_character_id_by_action_initiator_user_group_id(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
    ) -> List[int]:
        pass
