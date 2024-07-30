from abc import ABC, abstractmethod
from domain.entities.group import Group
from typing import List, Optional

class GroupRepository(ABC):
    @abstractmethod
    async def add(self, group: Group) -> None:
        pass
    
    @abstractmethod
    async def delete(self, group_id: int) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, group_id: int) -> Optional[Group]:
        pass
    
    @abstractmethod
    async def delete_groups_not_in_list(self, group_ids: List[int]) -> None:
        pass
    
    @abstractmethod
    async def get_all(self) -> List[int]:
        pass