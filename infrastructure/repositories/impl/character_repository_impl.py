from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func
from typing import Optional, List
from domain.entities import Character
from infrastructure.repositories import CharacterRepository
from infrastructure.database.orm import CharacterORM
from infrastructure.mappers.orm_to_domain import to_character_domain
from infrastructure.mappers.domain_to_orm import to_character_orm

class CharacterRepositoryImpl(CharacterRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, character: Character) -> int:
        character_orm = to_character_orm(character)
        self.session.add(character_orm)
        # 必须刷新以便获得cid
        await self.session.flush()
        return character_orm.id
    
    async def delete(self, character_id: int) -> None:
        stmt = delete(CharacterORM).where(CharacterORM.id == character_id)
        await self.session.execute(stmt)
    
    async def get_by_conditions(self, **conditions) -> List[Character]:
        stmt = select(CharacterORM)
        for attr, value in conditions.items():
            stmt = stmt.where(getattr(CharacterORM, attr) == value)
        result = await self.session.execute(stmt)
        characters_orm = result.scalars().all()
        characters = [to_character_domain(char_orm) for char_orm in characters_orm]
        return characters
    
    async def get_by_id(self, character_id: int) -> Optional[Character]:
        characters = await self.get_by_conditions(id=character_id)
        return characters[0] if characters else None

    async def get_by_name(self, name: str) -> Optional[Character]:
        characters = await self.get_by_conditions(name=name)
        return characters[0] if characters else None
    
    async def update(self, character: Character) -> None:
        stmt = select(CharacterORM).where(CharacterORM.id == character.id)
        result = await self.session.execute(stmt)
        character_orm = result.scalar_one()
        if character_orm:
            character_orm.name = character.name
            character_orm.pool_name = character.pool_name
            character_orm.image_name = character.image_name
            character_orm.image_path = character.image_path
            
    async def get_random_character(self) -> Optional[Character]:
        # 使用 select 和 func.random() 进行 ORM 查询
        stmt = select(CharacterORM).order_by(func.random()).limit(1)
        result = await self.session.execute(stmt)
        character_orm = result.scalar_one()
        if character_orm:
            character = to_character_domain(character_orm)
            return character
        return None

    async def count(self) -> int:
        stmt = select(func.count(CharacterORM.id))
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count
    
    async def search_character_by_partial_name(self, name: str) -> List[str]:
        # 模糊匹配，返回可能的所有name的列表
        stmt = select(CharacterORM).where(CharacterORM.name.like(f"%{name}%"))
        result = await self.session.execute(stmt)
        characters_orm = result.scalars().all()
        
        suggested_names = [char_orm.name for char_orm in characters_orm]
        return suggested_names

    async def get_character_name_by_character_id(
        self,
        character_id: List[int]
    ) -> List[str]:
        stmt = select(CharacterORM.name).where(CharacterORM.id.in_(character_id))
        result = await self.session.execute(stmt)
        names = [record.name for record in result]
        return names