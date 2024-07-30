from datetime import datetime
from domain.entities import UserGroup, Character, SingleEvent, DoubleEvent
from infrastructure.repositories import SingleRepository, DoubleRepository

class EventApplicationService:
    def __init__(self, single_repository: SingleRepository, double_repository: DoubleRepository):
        self.single_repo = single_repository
        self.double_repo = double_repository
        
    async def add_single_event(self, user_group: UserGroup, character: Character, event_type: str, result: str) -> None:
        new_single = SingleEvent(
            id=None,
            user_group_id=user_group.id,
            character_id=character.id,
            event_type=event_type,
            result=result,
            event_time=datetime.now()
        )
        await self.single_repo.add(new_single)
        
    async def add_double_event(self, initiator_ug: UserGroup, receiver_ug: UserGroup, initiator_character: Character, receiver_character: Character, event_type: str, result: str) -> None:
        new_double = DoubleEvent(
            id=None,
            group_id=initiator_ug.group_id,
            action_initiator_user_group_id=initiator_ug.id,
            action_receiver_user_group_id=receiver_ug.id,
            event_type=event_type,
            event_time=datetime.now(),
            initiator_current_character_id=initiator_character.id if initiator_character else None,
            receiver_current_character_id=receiver_character.id if receiver_character else None,
            result=result
        )
        await self.double_repo.add(new_double)