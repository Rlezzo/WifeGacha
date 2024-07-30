from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import CurrentUGC, UserGroup
from infrastructure.database.orm import CurrentORM
from infrastructure.repositories import CurrentRepository
from infrastructure.mappers import to_current_orm, to_current_domain, to_character_domain

class CurrentUserGroupCharacterRepositoryImpl(CurrentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, current_domain: CurrentUGC) -> None:
        cugc_orm = to_current_orm(current_domain)
        self.session.add(cugc_orm)

    async def get_by_ug(self, user_group: UserGroup) -> Optional[CurrentUGC]:
        stmt = select(CurrentORM).where(CurrentORM.user_group_id == user_group.id)
        result = await self.session.execute(stmt)
        current_orm = result.scalar_one_or_none()
        
        if current_orm:
            return to_current_domain(current_orm)
        return None
    
    async def get_by_ug_with_character_preloaded(self, user_group: UserGroup) -> Optional[CurrentUGC]:
        stmt = select(CurrentORM).options(
            selectinload(CurrentORM.character)
        ).where(CurrentORM.user_group_id == user_group.id)
        
        result = await self.session.execute(stmt)
        current_orm = result.scalar_one_or_none()
        
        if current_orm:
            character_orm = current_orm.character if current_orm.character else None
            current_character= to_character_domain(character_orm) if character_orm else None
            # 创建一个CurrentUserGroupCharacter实例，如果有必要的话可以手动赋值相关的user_group和character属性
            current_domain = to_current_domain(current_orm)
            current_domain.character = current_character
            return current_domain
        return None

    async def update(self, current_domain: CurrentUGC) -> None:
        stmt = select(CurrentORM).where(CurrentORM.id == current_domain.id)
        result = await self.session.execute(stmt)
        current_orm = result.scalar_one()
        current_orm.character_id = current_domain.character_id
        current_orm.update_time = current_domain.update_time