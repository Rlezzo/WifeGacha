from typing import List, Optional
from abc import ABC, abstractmethod
from domain.entities import UGCharacter, UserGroup, Character

class UserGroupCharacterRepository(ABC):
    @abstractmethod
    async def add(self, ug_character: UGCharacter) -> int:
        pass

    @abstractmethod
    async def get_without_stats(self, user_group: UserGroup, character: Character) -> Optional[UGCharacter]:
        pass
    
    @abstractmethod
    async def get_with_stats(self, user_group: UserGroup, character: Character) -> Optional[UGCharacter]:
        pass