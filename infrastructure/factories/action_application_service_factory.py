from typing import Optional
from application.services import ActionAppService
from infrastructure.database.connection import AsyncSession
from infrastructure.repositories.impl import StatsRepositoryImpl

class ActionServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self) -> Optional[ActionAppService]:
        stats_repo = StatsRepositoryImpl(self.session)
        action_sv = ActionAppService(
            stats_repository=stats_repo
        )
        return action_sv