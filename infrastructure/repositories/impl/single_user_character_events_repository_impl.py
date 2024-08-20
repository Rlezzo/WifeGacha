from typing import Optional, Tuple, List
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import SingleEvent
from infrastructure.repositories import SingleRepository
from infrastructure.database.orm import SingleORM, UserGroupORM
from infrastructure.mappers import to_single_orm


class SingleUserCharacterEventRepositoryImpl(SingleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, single_domain: SingleEvent) -> None:
        single_orm = to_single_orm(single_domain)
        self.session.add(single_orm)

    async def get_most_frequent_character_in_group(
            self,
            group_id: int,
            event_type: Optional[str] = None,
            result: Optional[str] = None
    ) -> Tuple[Optional[int], int]:
        '''
        获得本群中，满足条件的最多的角色和对应次数
        比如，抽老婆，重复，那么就会找到本群重复被抽到最多的角色，和被重复抽到几次
        '''
        stmt = (
            select(
                SingleORM.character_id,
                func.count(SingleORM.id).label('count')
            )
            .join(UserGroupORM, SingleORM.user_group_id == UserGroupORM.id)  # 筛出同群组单人事件表
            .filter(UserGroupORM.group_id == group_id)  # 筛选同一群组的user_group_id
        )

        if event_type:
            stmt = stmt.filter(SingleORM.event_type == event_type)
        if result:
            stmt = stmt.filter(SingleORM.result == result)

        stmt = stmt.group_by(SingleORM.character_id).order_by(func.count(SingleORM.id).desc()).limit(1)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return row.character_id, row.count
        return None, 0

    async def get_most_frequent_user_in_group(
            self,
            group_id: int,
            event_type: Optional[str] = None,
            result: Optional[str] = None
    ) -> Tuple[Optional[int], int]:
        # 构建基本查询语句
        stmt = (
            select(
                SingleORM.user_group_id.label('user_id'),
                func.count(SingleORM.id).label('count')
            )
            .join(UserGroupORM, SingleORM.user_group_id == UserGroupORM.id)
            .filter(UserGroupORM.group_id == group_id)
        )
        # 添加可选的事件类型过滤条件
        if event_type:
            stmt = stmt.filter(SingleORM.event_type == event_type)

        # 添加可选的事件结果过滤条件
        if result:
            stmt = stmt.filter(SingleORM.result == result)

        # 分组并按事件次数降序排序，限制结果为1条记录
        stmt = stmt.group_by(
            SingleORM.user_group_id
        ).order_by(
            func.count(SingleORM.id).desc()
        ).limit(1)

        # 执行查询语句
        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return row.user_id, row.count
        return None, 0

    async def get_event_count_by_user_group_id(
            self,
            user_group_id: int,
            event_type: str,
            result: Optional[str] = None,
            character_id: Optional[int] = None
    ) -> int:
        stmt = (
            select(
                # 去除重复项
                func.count(distinct(SingleORM.character_id)).label('unique_character_count')
            )
            .filter(SingleORM.user_group_id == user_group_id)
            .filter(SingleORM.event_type == event_type)
        )

        if result:
            stmt = stmt.filter(SingleORM.result == result)
        if character_id:
            stmt = stmt.filter(SingleORM.character_id == character_id)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row and row.event_count:
            return row.event_count
        return 0


    async def get_character_id_by_user_group_id(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
    ) -> List[int]:
        # 构造查询
        stmt = (
            select(distinct(SingleORM.character_id))  # 使用 distinct 来获取不同的 character_id
            .filter(SingleORM.user_group_id == user_group_id)
            .filter(SingleORM.event_type == event_type)
        )
        # 如果指定了 result，则添加相应的过滤条件
        if result:
            stmt = stmt.filter(SingleORM.result == result)
        # 执行查询
        result = await self.session.execute(stmt)
        character_ids = [row[0] for row in result.fetchall()]  # 提取所有行并只取 character_id
        # 返回包含唯一 character_id 的列表
        return character_ids
