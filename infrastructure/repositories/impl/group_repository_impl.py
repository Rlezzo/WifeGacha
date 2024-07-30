from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import Group
from infrastructure.repositories import GroupRepository
from infrastructure.database.orm import GroupORM
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional

class GroupRepositoryImpl(GroupRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, group: Group) -> None:
        group_orm = GroupORM(id=group.id)
        self.session.add(group_orm)
    
    async def delete(self, group_id: int) -> None:
        stmt = select(GroupORM).where(GroupORM.id == group_id)
        result = await self.session.execute(stmt)
        group_orm = result.scalar_one_or_none()
        if group_orm:
            self.session.delete(group_orm)
    
    async def get_by_id(self, group_id: int) -> Optional[Group]:
        stmt = select(GroupORM).where(GroupORM.id == group_id)
        result = await self.session.execute(stmt)
        group_orm = result.scalar_one_or_none()
        if group_orm:
            return Group(id=group_orm.id)
        return None

    async def delete_groups_not_in_list(self, group_ids: List[int]) -> None:
        # 删除不在 group_ids 列表中的群
        stmt = delete(GroupORM).where(GroupORM.id.not_in(group_ids))
        await self.session.execute(stmt)
    
    async def get_all(self) -> List[int]:
        stmt = select(GroupORM.id)
        result = await self.session.execute(stmt)
        group_ids = [row[0] for row in result.fetchall()]
        return group_ids