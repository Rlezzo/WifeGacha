from typing import List, Optional, Union
from domain.entities import Character
from infrastructure.repositories import CharacterRepository

class CharacterApplicationService:
    def __init__(self, character_repository: CharacterRepository):
        self.character_repository = character_repository

    async def add_character(self, name: str, pool_name: str, image_name: str, image_path: str) -> Optional[Character]:
        # 同名角色不能重复添加
        existing_character_by_name = await self.character_repository.get_by_name(name)
        if existing_character_by_name:
            raise Exception(f"Character '{name}' already exists.")
        character = Character(
            id=None,
            name=name,
            pool_name=pool_name,
            image_name=image_name,
            image_path=image_path
        )
        character.id = await self.character_repository.add(character)
        return character

    async def delete_charactera_by_name(self, character_name: str) -> tuple[str, str]:
        existing_character = await self.character_repository.get_by_name(character_name)
        if existing_character:
            await self.character_repository.delete(existing_character.id)
            return existing_character.image_name, existing_character.pool_name
        else:
            raise Exception(f"Character '{character_name}' does not exist.")
        
    async def get_character_by_id(self, character_id: int) -> Optional[Character]:
        return await self.character_repository.get_by_id(character_id)
    
    async def get_character_by_name(self, name: str) -> Optional[Character]:
        return await self.character_repository.get_by_name(name)

    async def update_character(self, character: Character) -> None:
        await self.character_repository.update(character)
        
    async def get_random_character(self) -> Optional[Character]:
        return await self.character_repository.get_random_character()
    
    async def count(self) -> int:
        return await self.character_repository.count()
    
    async def search_character_by_partial_name(self, name: str) -> Union[Optional[Character], List[str]]:
        # 精确匹配
        character = await self.character_repository.get_by_name(name)
        if character:
            return character
        # 没找到，模糊匹配
        return await self.character_repository.search_character_by_partial_name(name)

    async def get_character_name(
            self,
            character_id: List[int]
    ) -> List[str]:
        return await self.character_repository.get_character_name_by_character_id(character_id)
