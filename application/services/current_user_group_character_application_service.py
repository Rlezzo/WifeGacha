from typing import Optional
from datetime import datetime
from infrastructure.repositories import CurrentRepository
from domain.entities import CurrentUGC, UserGroup, Character


class CurrentUserGroupCharacterApplicationService:
    def __init__(self, current_user_group_character_repository: CurrentRepository):
        self.current_ugc_repo = current_user_group_character_repository
    
    async def get_current_character(self, user_group: UserGroup) -> Optional[Character]:
        # 检查current_ugc是否存在：
        current_ugc = await self.current_ugc_repo.get_by_ug_with_character_preloaded(user_group)
        # 如果不存在，或者老婆为空，或者日期不是今天，返回None
        if not current_ugc or not current_ugc.character_id or current_ugc.update_time.date() != datetime.now().date():
            return None
        # 否则返回今日老婆
        return current_ugc.character
    
    async def add_or_update_current_character(self, user_group: UserGroup, character: Character) -> None:
        # 是否存在
        existing_current_ugc = await self.current_ugc_repo.get_by_ug(user_group)
        if not existing_current_ugc:
            # 不存在，新建
            new_cugc = CurrentUGC(
                id=None,
                user_group_id=user_group.id,
                character_id=character.id,
                update_time=datetime.now()
            )
            await self.current_ugc_repo.add(new_cugc)
            return
        # 否则，更新cid和time
        existing_current_ugc.character_id = character.id
        existing_current_ugc.update_time = datetime.now()
        await self.current_ugc_repo.update(existing_current_ugc)
        
    
    async def remove_cid_by_user_group(self, user_group: UserGroup) -> None:
        # 清除角色id
        existing_current_ugc = await self.current_ugc_repo.get_by_ug(user_group)
        if existing_current_ugc:
            existing_current_ugc.character_id = None
            existing_current_ugc.update_time = datetime.now()
            # 更新角色和时间
            await self.current_ugc_repo.update(existing_current_ugc)
