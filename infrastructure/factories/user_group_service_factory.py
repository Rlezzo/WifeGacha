from typing import Optional
from application.services import UserGroupAppService
from infrastructure.database.connection import AsyncSession
from infrastructure.repositories.impl import UserRepositoryImpl, GroupRepositoryImpl, UserGroupRepositoryImpl

class UserGroupServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self) -> Optional[UserGroupAppService]:
        user_repo = UserRepositoryImpl(self.session)
        group_repo = GroupRepositoryImpl(self.session)
        user_group_repo = UserGroupRepositoryImpl(self.session)
        ug_service = UserGroupAppService(
            user_repository=user_repo,
            group_repository=group_repo,
            user_group_repository=user_group_repo
        )
        return ug_service