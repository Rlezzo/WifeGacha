from typing import Optional
from application.services import EventAppService
from infrastructure.database.connection import AsyncSession
from infrastructure.repositories.impl import SingleRepositoryImpl, DoubleRepositoryImpl


class EventServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self) -> Optional[EventAppService]:
        single_repo = SingleRepositoryImpl(self.session)
        double_repo = DoubleRepositoryImpl(self.session)
        event_service = EventAppService(
            single_repository=single_repo,
            double_repository=double_repo
        )
        return event_service