from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import UserGroup
from infrastructure.repositories import UserGroupRepository
from infrastructure.database.orm import UserGroupORM
from sqlalchemy.future import select
from typing import Optional, List
from infrastructure.mappers import to_user_group_orm, to_user_group_domain

class UserGroupRepositoryImpl(UserGroupRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, user_group: UserGroup) -> int:
        user_group_orm = to_user_group_orm(user_group)
        self.session.add(user_group_orm)
        await self.session.flush()
        return user_group_orm.id
    
    async def delete(self, user_group_id: int) -> None:
        stmt = select(UserGroupORM).where(UserGroupORM.id == user_group_id)
        result = await self.session.execute(stmt)
        user_group_orm = result.scalar_one_or_none()
        if user_group_orm:
            self.session.delete(user_group_orm)
    
    async def get_by_conditions(self, **conditions) -> List[UserGroup]:
        stmt = select(UserGroupORM)
        for attr, value in conditions.items():
            stmt = stmt.where(getattr(UserGroupORM, attr) == value)
        result = await self.session.execute(stmt)
        orm_list = result.scalars().all()
        return [to_user_group_domain(orm) for orm in orm_list]

    async def get_by_id(self, user_group_id: int) -> Optional[UserGroup]:
        results = await self.get_by_conditions(id=user_group_id)
        return results[0] if results else None
    
    async def get_by_uid_and_gid(self, user_id: int, group_id: int) -> Optional[UserGroup]:
        results = await self.get_by_conditions(user_id=user_id, group_id=group_id)
        return results[0] if results else None

    async def get_by_user_id(self, user_id: int) -> List[UserGroup]:
        return await self.get_by_conditions(user_id=user_id)
    
    async def get_by_group_id(self, group_id: int) -> List[UserGroup]:
        return await self.get_by_conditions(group_id=group_id)
