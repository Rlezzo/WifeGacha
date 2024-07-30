from abc import ABC, abstractmethod
from typing import Optional
from domain.entities import CurrentUGC, UserGroup

class CurrentUserGroupCharacterRepository(ABC):
    @abstractmethod
    async def add(self, current_domain: CurrentUGC) -> None:
        pass

    @abstractmethod
    async def get_by_ug(self, user_group: UserGroup) -> Optional[CurrentUGC]:
        pass
    
    @abstractmethod
    async def get_by_ug_with_character_preloaded(self, user_group: UserGroup) -> Optional[CurrentUGC]:
        pass

    @abstractmethod
    async def update(self, current_domain: CurrentUGC) -> None:
        pass