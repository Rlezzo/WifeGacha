from typing import Optional
from infrastructure.database.connection import AsyncSession
from application.services import UGCharacterAppService
from infrastructure.repositories.impl import UGCharacterRepositoryImpl, StatsRepositoryImpl

class UserGroupCharacterServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self) -> Optional[UGCharacterAppService]:
        ugc_repo = UGCharacterRepositoryImpl(self.session)
        ugc_stats_repo = StatsRepositoryImpl(self.session)
        ugc_sv = UGCharacterAppService(
            user_group_character_repository=ugc_repo,
            stats_repository=ugc_stats_repo
        )
        return ugc_sv