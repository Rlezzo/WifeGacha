from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import User
from infrastructure.repositories import UserRepository
from infrastructure.database.orm import UserORM
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List, Optional

class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add(self, user: User) -> None:
        user_orm = UserORM(id=user.id)
        self.session.add(user_orm)
    
    async def delete(self, user_id: int) -> None:
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        user_orm = result.scalar_one_or_none()
        if user_orm:
            self.session.delete(user_orm)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(UserORM).where(UserORM.id == user_id)
        result = await self.session.execute(stmt)
        user_orm = result.scalar_one_or_none()
        if user_orm:
            return User(id=user_orm.id)
        return None
    
    async def delete_users_not_in_list(self, user_ids: List[int]) -> None:
        # 删除不在 user_ids 列表中的指定 group_id 的用户
        stmt = delete(UserORM).where(UserORM.id.not_in(user_ids))
        await self.session.execute(stmt)
