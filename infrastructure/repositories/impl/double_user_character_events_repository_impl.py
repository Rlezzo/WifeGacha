from typing import Optional, Tuple, List
from sqlalchemy import func, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities import DoubleEvent
from infrastructure.repositories import DoubleRepository
from infrastructure.database.orm import DoubleORM
from infrastructure.mappers import to_double_orm

class DoubleUserCharacterEventRepositoryImpl(DoubleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, double_domain: DoubleEvent) -> None:
        double_orm = to_double_orm(double_domain)
        self.session.add(double_orm)
        
    async def get_most_frequent_character_in_group(self, group_id: int, event_type: Optional[str] = None, result: Optional[str] = None, receiver: bool = True) -> Tuple[Optional[int], int]:
        # 根据 receiver 参数决定查询接收者角色还是发起者角色
        character_id_column = DoubleORM.receiver_current_character_id.label('character_id') if receiver else DoubleORM.initiator_current_character_id.label('character_id')

        stmt = (
            select(
                character_id_column,
                func.count(DoubleORM.id).label('count')
            )
            .filter(DoubleORM.group_id == group_id)  # 筛选同一群组的group_id
        )

        if event_type:
            stmt = stmt.filter(DoubleORM.event_type == event_type)
        if result:
            stmt = stmt.filter(DoubleORM.result == result)

        stmt = stmt.group_by(character_id_column).order_by(func.count(DoubleORM.id).desc()).limit(1)
        
        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return row.character_id, row.count
        return None, 0
    

    async def get_most_frequent_user(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
        is_initiator: bool = True
    ) -> Tuple[Optional[int], int]:
        if is_initiator:
            # 查找接收人
            target_column = DoubleORM.action_receiver_user_group_id.label('target_user_id')
            filter_column = DoubleORM.action_initiator_user_group_id
        else:
            # 查找发起人
            target_column = DoubleORM.action_initiator_user_group_id.label('target_user_id')
            filter_column = DoubleORM.action_receiver_user_group_id

        # 构建基本查询语句
        stmt = select(
            target_column,
            func.count(DoubleORM.id).label('count')
        ).filter(
            filter_column == user_group_id,
            DoubleORM.event_type == event_type
        )

        # 添加可选的事件结果过滤条件
        if result:
            stmt = stmt.filter(DoubleORM.result == result)

        # 分组并按事件次数降序排序，限制结果为1条记录
        stmt = stmt.group_by(
            target_column
        ).order_by(
            func.count(DoubleORM.id).desc()
        ).limit(1)

        # 执行查询语句
        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return row.target_user_id, row.count
        return None, 0
    
    async def get_event_count_in_group(
        self,
        group_id: int,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None,
        receiver: bool = True
    ) -> int:
        character_column = DoubleORM.receiver_current_character_id if receiver else DoubleORM.initiator_current_character_id
        
        stmt = (
            select(
                func.count(DoubleORM.id).label('event_count')
            )
            .filter(DoubleORM.group_id == group_id)  # 直接在 DoubleORM 上进行 group_id 过滤
            .filter(DoubleORM.event_type == event_type)
        )

        if result:
            stmt = stmt.filter(DoubleORM.result == result)
        if character_id:
            stmt = stmt.filter(character_column == character_id)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row and row.event_count:
            return row.event_count
        return 0
    
    async def get_event_count_by_user_group_id(
        self,
        user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
        character_id: Optional[int] = None,
        is_user_receiver: bool = False,
        is_character_receiver: bool = True
    ) -> int:
        # 根据 is_character_receiver 参数决定角色是接收者还是发起者, 默认角色是接受者
        character_column = DoubleORM.receiver_current_character_id if is_character_receiver else DoubleORM.initiator_current_character_id
        # 根据 is_user_receiver 参数决定用户是接收者还是发起者， 默认用户是发起者
        user_group_column = DoubleORM.action_receiver_user_group_id if is_user_receiver else DoubleORM.action_initiator_user_group_id
        
        stmt = (
            select(
                func.count(DoubleORM.id).label('event_count')
            )
            .filter(user_group_column == user_group_id)
            .filter(DoubleORM.event_type == event_type)
        )

        if result:
            stmt = stmt.filter(DoubleORM.result == result)
        if character_id:
            stmt = stmt.filter(character_column == character_id)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row and row.event_count:
            return row.event_count
        return 0

    async def get_current_receiver_character_id_by_action_initiator_user_group_id(
        self,
        action_initiator_user_group_id: int,
        event_type: str,
        result: Optional[str] = None,
    ) -> List[int]:
        # 构造查询
        stmt = (
            select(distinct(DoubleORM.receiver_current_character_id))  # 使用 distinct 来获取不同的 receiver_current_character_id
            .filter(DoubleORM.action_initiator_user_group_id == action_initiator_user_group_id)
            .filter(DoubleORM.event_type == event_type)
        )
        # 如果指定了 result，则添加相应的过滤条件
        if result:
            stmt = stmt.filter(DoubleORM.result == result)
        # 执行查询
        result = await self.session.execute(stmt)
        receiver_current_character_ids = [row[0] for row in result.fetchall()]  # 提取所有行并只取 receiver_current_character_id
        # 返回包含唯一 receiver_current_character_id 的列表
        return receiver_current_character_ids