from typing import Optional, Tuple, Union, List
from domain.entities import UserGroup, Character, ActionType, AcqMethod
from infrastructure.repositories import (
    SingleRepository, 
    DoubleRepository, 
    CharacterRepository, 
    StatsRepository
)
class StatisticsApplicationService:
    def __init__(
        self, 
        single_repository: SingleRepository, 
        double_repository: DoubleRepository, 
        character_repository: CharacterRepository,
        stats_repository: StatsRepository
        ):
        self.single_repo = single_repository
        self.character_repo = character_repository
        self.double_repo = double_repository
        self.stats_repo = stats_repository
        
    async def get_most_frequent_character_in_group(
        self,
        user_group: UserGroup,
        event_type: Optional[str] = None,
        result: Optional[str] = None,
        is_double: bool = False,
        receiver: Optional[bool] = True
    ) -> Tuple[Optional[Character], int]:
        if is_double:
            # 调用双人事件表的方法
            character_id, count = await self.double_repo.get_most_frequent_character_in_group(
                user_group.group_id, event_type, result, receiver
            )
        else:
            # 调用单人事件表的方法
            character_id, count = await self.single_repo.get_most_frequent_character_in_group(
                user_group.group_id, event_type, result
            )

        if character_id:
            character = await self.character_repo.get_by_id(character_id)
            return character, count
        return None, 0

    async def get_most_frequent_user_group_id(
        self,
        user_group: UserGroup,
        event_type: str,
        result: Optional[str] = None,
        is_initiator: bool = True,
        is_double: bool = True
    ) -> Tuple[Optional[int], int]:
        """
        double:例如查询ug作为发起者，牛老婆事件，成功，谁作为对象次数最多，返回对象id和次数
        single:例如查询抽老婆，谁抽的最多，返回id和次数
        """
        if is_double:
            user_group_id, count = await self.double_repo.get_most_frequent_user(
                user_group_id=user_group.id,
                event_type=event_type,
                result=result,
                is_initiator=is_initiator
            )
            return user_group_id, count
        else:
            user_group_id, count = await self.single_repo.get_most_frequent_user_in_group(
                group_id=user_group.group_id,
                event_type=event_type,
                result=result
            )
            return user_group_id, count
    
    async def get_top_action_count_character_in_group(
        self,
        user_group: UserGroup,
        action: ActionType
    ) -> Tuple[Optional[Character], Optional[int], int]:
        character_id, count = await self.stats_repo.get_top_action_count_character_in_group(
            group_id=user_group.group_id,
            action=action
        )
        if character_id:
            character = await self.character_repo.get_by_id(character_id)
            return character, count
        return None, 0
    
    async def get_total_count_by_type(
        self, 
        user_group: UserGroup, 
        count_type: Union[AcqMethod, ActionType],
        character: Optional[Character] = None,
        for_entire_group: bool = True
    ) -> int:
        """
        默认查一个群的总数，反之查个人的
        """
        if for_entire_group:
            return await self.stats_repo.get_total_count_in_group(
                group_id=user_group.group_id,
                count_type=count_type,
                character_id=character.id if character else None
            )
        else:
            return await self.stats_repo.get_total_count_by_user_group_id(
                user_group_id=user_group.id,
                count_type=count_type,
                character_id=character.id if character else None
            )
            

    async def get_double_event_count(
        self,
        user_group: UserGroup,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None,
        is_user_receiver: bool = False,
        is_character_receiver: bool = True,
        for_entire_group: bool = True
    ) -> int:
        if for_entire_group:
            return await self.double_repo.get_event_count_in_group(
                group_id=user_group.group_id,
                event_type=event_type,
                result=result,
                character_id=character_id,
                receiver=is_character_receiver
            )
        else:
            return await self.double_repo.get_event_count_by_user_group_id(
                user_group_id=user_group.id,
                event_type=event_type,
                result=result,
                character_id=character_id,
                is_user_receiver=is_user_receiver,
                is_character_receiver=is_character_receiver
            )
            
    async def get_single_event_count(
        self,
        user_group: UserGroup,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None
    ) -> int:
        return await self.single_repo.get_event_count_by_user_group_id(
            user_group_id=user_group.id,
            event_type=event_type,
            result=result,
            character_id=character_id
        )

    # 获得用户抽老婆得到的所有老婆ID
    async def get_user_character_ids(
        self,
        user_group: UserGroup,
        event_type: str,
        result: Optional[str] = None
    ) -> List[int]:
        # 获取抽卡ID
        return await self.single_repo.get_character_id_by_user_group_id(
            user_group_id=user_group.id,
            event_type=event_type,
            result=result,
        )

    # 获得发起者（牛老婆/交换老婆）成功取所得的老婆ID
    async def get_user_initiator_character_ids(
        self,
        initiator_ug: UserGroup,
        event_type: str,
        result: Optional[str] = None
    ) -> List[int]:
        # 获取抽卡ID
        return await self.double_repo.get_receiver_current_character_ids_by_action_initiator_user_group_id(
            action_initiator_user_group_id=initiator_ug.id,
            event_type=event_type,
            result=result,
        )

    # 获得同意者（交换老婆）成功取所得的老婆ID
    async def get_user_receiver_character_ids(
        self,
        receiver_ug: UserGroup,
        event_type: str,
        result: Optional[str] = None
    ) -> List[int]:
        # 获取抽卡ID
        return await self.double_repo.get_initiator_current_character_ids_by_action_receiver_user_group_id(
            action_receiver_user_group_id=receiver_ug.id,
            event_type=event_type,
            result=result,
        )
