from abc import ABC, abstractmethod
from domain.entities import UserGroup
from typing import Optional, List

class UserGroupRepository(ABC):
    @abstractmethod
    async def add(self, user_group: UserGroup) -> int:
        pass
    
    @abstractmethod
    async def delete(self, user_group_id: int) -> None:
        pass
    
    @abstractmethod
    async def get_by_conditions(self, **conditions) -> List[UserGroup]:
        pass

    @abstractmethod
    async def get_by_id(self, user_group_id: int) -> Optional[UserGroup]:
        pass
    
    @abstractmethod
    async def get_by_uid_and_gid(self, user_id: int, group_id: int) -> Optional[UserGroup]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[UserGroup]:
        pass
    
    @abstractmethod
    async def get_by_group_id(self, group_id: int) -> List[UserGroup]:
        pass
