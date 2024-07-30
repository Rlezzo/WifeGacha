# 日老婆服务
from domain.entities import Character, UserGroup, ActionType, ACTION_FIELD
from infrastructure.repositories import StatsRepository

class ActionApplicationService:
    def __init__(self, stats_repository: StatsRepository):
        self.stats_repo = stats_repository
        
    async def update_action_count(self, user_group: UserGroup, character: Character, action_type: ActionType) -> None:
        stats = await self.stats_repo.get_by_user_group_character(user_group, character)
        if not stats:
            raise Exception("未找到stats, 不应该出现的异常!请检查主方法逻辑！")
        # 更新stats里的数据
        field_name = ACTION_FIELD[action_type]
        setattr(stats, field_name, getattr(stats, field_name) + 1)
        await self.stats_repo.update_action_count(stats)