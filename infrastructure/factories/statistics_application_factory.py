from typing import Optional
from application.services import StatisticsAppService
from infrastructure.database.connection import AsyncSession
from infrastructure.repositories.impl import (
    CharacterRepositoryImpl, 
    SingleRepositoryImpl, 
    DoubleRepositoryImpl, 
    StatsRepositoryImpl
)
class StatisticsServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create(self) -> Optional[StatisticsAppService]:
        character_repo = CharacterRepositoryImpl(self.session)
        single_repo = SingleRepositoryImpl(self.session)
        double_repo = DoubleRepositoryImpl(self.session)
        stats_repo = StatsRepositoryImpl(self.session)
        
        statistics_sv = StatisticsAppService(
            character_repository=character_repo,
            single_repository=single_repo,
            double_repository=double_repo,
            stats_repository=stats_repo
        )
        return statistics_sv