from abc import ABC, abstractmethod
from domain.entities import Character
from typing import Optional, List

class CharacterRepository(ABC):
    @abstractmethod
    async def add(self, character: Character) -> int:
        pass
    
    @abstractmethod
    async def delete(self, character_id: int) -> None:
        pass
    
    @abstractmethod
    async def get_by_conditions(self, **conditions) -> List[Character]:
        pass
    
    @abstractmethod
    async def get_by_id(self, character_id: int) -> Optional[Character]:
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Character]:
        pass
    
    @abstractmethod
    async def update(self, character: Character) -> None:
        pass
    
    @abstractmethod
    async def get_random_character(self) -> Optional[Character]:
        pass
    
    @abstractmethod
    async def count(self) -> int:
        pass
    
    abstractmethod
    async def search_character_by_partial_name(self, name: str) -> List[str]:
        pass