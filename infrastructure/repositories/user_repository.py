from abc import ABC, abstractmethod
from domain.entities import User
from typing import List, Optional

class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> None:
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def delete_users_not_in_list(self, user_ids: List[int]) -> None:
        pass