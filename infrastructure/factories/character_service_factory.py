from typing import Optional
from application.services import CharacterAppService
from infrastructure.database.connection import AsyncSession
from infrastructure.repositories.impl import CharacterRepositoryImpl

class CharacterServiceFactory:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self) -> Optional[CharacterAppService]:
        character_repo = CharacterRepositoryImpl(self.session)
        character_sv = CharacterAppService(
            character_repository=character_repo
        )
        return character_sv