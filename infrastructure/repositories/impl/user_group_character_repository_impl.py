from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.repositories import UGCharacterRepository
from domain.entities import UGCharacter, UserGroup, Character
from infrastructure.database.orm import UGCharacterORM, StatsORM
from infrastructure.mappers import to_ug_character_orm, to_ug_character_domain, to_stats_domain

class UserGroupCharacterRepositoryImpl(UGCharacterRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, ug_character: UGCharacter) -> int:
        ug_character_orm = to_ug_character_orm(ug_character)
        self.session.add(ug_character_orm)
        # 这里必须刷新，为了获取id新建stats子表
        await self.session.flush()
        return ug_character_orm.id

    async def get_without_stats(self, user_group: UserGroup, character: Character) -> Optional[UGCharacter]:
        stmt = select(UGCharacterORM).filter(
            UGCharacterORM.user_group_id == user_group.id,
            UGCharacterORM.character_id == character.id
        )
        
        result = await self.session.execute(stmt)
        ug_character_orm = result.scalar_one_or_none()

        if ug_character_orm:
            return to_ug_character_domain(ug_character_orm)
        return None
    
    async def get_with_stats(self, user_group: UserGroup, character: Character) -> Optional[UGCharacter]:
        stmt = select(UGCharacterORM).options(
            selectinload(UGCharacterORM.stats)
        ).filter(
            UGCharacterORM.user_group_id == user_group.id,
            UGCharacterORM.character_id == character.id
        )
        
        result = await self.session.execute(stmt)
        ug_character_orm = result.scalar_one_or_none()

        if ug_character_orm:
            # 在这里，我们手动创建UserGroupCharacter领域模型实例，并填充stats关系
            stats_orm: StatsORM = ug_character_orm.stats if ug_character_orm.stats else None
            stats = to_stats_domain(stats_orm) if stats_orm else None

            ug_character_domain = to_ug_character_domain(ug_character_orm)
            ug_character_domain.stats = stats
            return ug_character_domain
        return None