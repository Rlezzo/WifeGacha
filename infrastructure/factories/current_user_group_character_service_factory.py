from typing import Optional
from application.services import CurrentAppService
from infrastructure.database.connection import AsyncSession
from infrastructure.repositories.impl import CurrentRepositoryImpl

class CurrentUserGroupCharacterServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self) -> Optional[CurrentAppService]:
        current_ugc_repo = CurrentRepositoryImpl(self.session)
        current_ugc_sv = CurrentAppService(
            current_user_group_character_repository=current_ugc_repo
        )
        return current_ugc_sv