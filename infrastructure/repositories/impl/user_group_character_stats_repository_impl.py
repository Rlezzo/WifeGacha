from typing import Optional, Tuple, Union
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import Stats, UserGroup, Character, ActionType, AcqMethod, ACTION_FIELD, ACQ_FIELD
from infrastructure.database.orm import StatsORM, UserGroupORM
from infrastructure.repositories import StatsRepository
from infrastructure.mappers import to_stats_orm, to_stats_domain

class UserGroupCharacterStatsRepositoryImpl(StatsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, stats_domain: Stats) -> None:
        stats_orm = to_stats_orm(stats_domain)
        self.session.add(stats_orm)

    async def update_acquired_count(self, stats_domain: Stats) -> None:
        stmt = select(StatsORM).where(StatsORM.id == stats_domain.id)
        result = await self.session.execute(stmt)
        stats_orm = result.scalar_one_or_none()
        if stats_orm:
            # 更新获取数
            stats_orm.lastest_acquisition_time = stats_domain.lastest_acquisition_time
            stats_orm.draw_count = stats_domain.draw_count
            stats_orm.acquired_by_ex_count = stats_domain.acquired_by_ex_count
            stats_orm.acquired_by_ntr_count = stats_domain.acquired_by_ntr_count
    
    async def update_action_count(self, stats_domain: Stats) -> None:
        stmt = select(StatsORM).where(StatsORM.id == stats_domain.id)
        result = await self.session.execute(stmt)
        stats_orm = result.scalar_one_or_none()
        if stats_orm:
            # 更新mating_count
            stats_orm.mating_count=stats_domain.mating_count
            stats_orm.divorce_count=stats_domain.divorce_count
        
    async def get_by_user_group_character(self, user_group: UserGroup, character: Character) -> Optional[Stats]:
        stmt = select(StatsORM).where(
            StatsORM.user_group_id == user_group.id,
            StatsORM.character_id == character.id
        )
        result = await self.session.execute(stmt)
        stats_orm = result.scalar_one_or_none()
        if stats_orm:
            return to_stats_domain(stats_orm)
        return None
    
    async def get_top_action_count_character_in_group(
        self, 
        group_id: int, 
        action: ActionType
    ) -> Tuple[Optional[int], int]:
        field_name = ACTION_FIELD[action]
        stmt = (
            select(
                StatsORM.character_id,
                getattr(StatsORM, field_name).label('action_count')
            )
            .join(UserGroupORM, StatsORM.user_group_id == UserGroupORM.id)
            .filter(UserGroupORM.group_id == group_id)
            .order_by(getattr(StatsORM, field_name).desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return row.character_id, row.action_count
        return None, 0

    async def get_total_count_in_group(
        self, 
        group_id: int, 
        count_type: Union[AcqMethod, ActionType],
        character_id: Optional[int] = None
    ) -> int:
        """
        获得本群中，指定项的总数
        不限定角色，查抽取数，所有角色的所有人抽取数之和
        限定角色，查抽取数，某个角色所有人抽取数之和
        """
        if isinstance(count_type, AcqMethod):
            field_name = ACQ_FIELD[count_type]
        elif isinstance(count_type, ActionType):
            field_name = ACTION_FIELD[count_type]
        
        stmt = (
            select(
                func.sum(getattr(StatsORM, field_name)).label('total_count')
            )
            .join(UserGroupORM, StatsORM.user_group_id == UserGroupORM.id)
            .filter(UserGroupORM.group_id == group_id)
        )
        
        if character_id is not None:
            stmt = stmt.filter(StatsORM.character_id == character_id)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row and row.total_count:
            return row.total_count
        return 0
    
    async def get_total_count_by_user_group_id(
        self, 
        user_group_id: int, 
        count_type: Union[AcqMethod, ActionType],
        character_id: Optional[int] = None
    ) -> int:
        if isinstance(count_type, AcqMethod):
            field_name = ACQ_FIELD[count_type]
        elif isinstance(count_type, ActionType):
            field_name = ACTION_FIELD[count_type]
        
        stmt = (
            select(
                func.sum(getattr(StatsORM, field_name)).label('total_count')
            )
            .filter(StatsORM.user_group_id == user_group_id)
        )
        
        if character_id is not None:
            stmt = stmt.filter(StatsORM.character_id == character_id)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row and row.total_count:
            return row.total_count
        return 0