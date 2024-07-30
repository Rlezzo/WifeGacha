from typing import Optional
from datetime import datetime
from domain.entities import Character, UserGroup, UGCharacter, Stats, AcqMethod, ACQ_FIELD, ACTION_FIELD
from infrastructure.repositories import UGCharacterRepository, StatsRepository

class UserGroupCharacterApplicationService:
    def __init__(self, user_group_character_repository: UGCharacterRepository, stats_repository: StatsRepository):
        self.ugc_repo = user_group_character_repository
        self.stats_repo = stats_repository
    
    async def get_user_group_character_stats(self, user_group: UserGroup, character: Character) -> Optional[Stats]:
        return await self.stats_repo.get_by_user_group_character(user_group, character)
    
    async def get_user_group_character_with_stats(self, user_group: UserGroup, character: Character) -> Optional[UGCharacter]:
        return await self.ugc_repo.get_with_stats(user_group, character)
    
    async def has_character(self, user_group: UserGroup, character: Character) -> bool:
        return bool(await self.ugc_repo.get_without_stats(user_group, character))
    
    async def add_or_update_character_by_acquisition_method(self, user_group: UserGroup, character: Character, acq_method: AcqMethod) -> None:
        # 是否存在
        existing_ugc = await self.ugc_repo.get_with_stats(user_group, character)
        if existing_ugc:
            stats: Stats = existing_ugc.stats
            # 更新stats里的数据
            field_name = ACQ_FIELD[acq_method]
            setattr(stats, field_name, getattr(stats, field_name) + 1)
            stats.lastest_acquisition_time = datetime.now()
            await self.stats_repo.update_acquired_count(stats)
            return
        # 不存在，新添加ug和c的关联
        new_ugc = UGCharacter(
            id=None,
            user_group_id=user_group.id,
            character_id=character.id,
            acquisition_time=datetime.now()
        )
        # 获得数据库生成的ugc_id
        new_ugc.id = await self.ugc_repo.add(new_ugc)
        # 使用 ACQ_METHOD_TO_FIELD 生成初始化所有计数字段
        stats_acq_count_init = {field: 0 for field in ACQ_FIELD.values()}
        # 动态设置对应的计数字段
        stats_acq_count_init[ACQ_FIELD[acq_method]] = 1
        
        # 使用 ACQ_METHOD_TO_FIELD 生成初始化所有计数字段
        stats_action_count_init = {field: 0 for field in ACTION_FIELD.values()}
        
        # 新建stats
        new_ugc_stats = Stats(
            id=None,
            user_group_character_id=new_ugc.id,
            user_group_id=user_group.id,
            character_id=character.id,
            lastest_acquisition_time=datetime.now(),
            **stats_acq_count_init,
            **stats_action_count_init
        )
        await self.stats_repo.add(new_ugc_stats)
