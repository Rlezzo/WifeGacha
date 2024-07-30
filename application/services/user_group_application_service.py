from typing import List, Optional
from domain.entities import User, Group, UserGroup
from infrastructure.repositories import UserRepository, GroupRepository, UserGroupRepository

class UserGroupApplicationService:
    def __init__(self, user_repository: UserRepository, group_repository: GroupRepository, user_group_repository: UserGroupRepository):
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.user_group_repo = user_group_repository

    async def add_and_get_user_group(self, user_id: int, group_id: int) -> UserGroup:
        # 添加user_group，如果存在只是查询了一下，不会重复添加，如果不存在就添加了新用户
        existing_user_group = await self.user_group_repo.get_by_uid_and_gid(user_id, group_id)
        if existing_user_group:
            # 如果存在直接返回
            return existing_user_group
        
        # 不存在user_group，检查user是否存在，不存在就添加
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            user = User(id=user_id)
            await self.user_repository.add(user)
        
        # 检查group是否存在，如果不存在则添加
        group = await self.group_repository.get_by_id(group_id)
        if not group:
            group = Group(id=group_id)
            await self.group_repository.add(group)
        
        # 创建并添加UserGroup
        user_group = UserGroup(id=None, user_id=user_id, group_id=group_id)
        # 把新用户持久化到数据库
        user_group.id = await self.user_group_repo.add(user_group)
        return user_group
    
    async def delete_user_group(self, user_id: int, group_id: int) -> None:
        # 删除UserGroup
        user_group = await self.user_group_repo.get_by_uid_and_gid(user_id, group_id)
        if user_group:
            await self.user_group_repo.delete(user_group.id)

        # 检查并删除孤立的用户
        remaining_user_groups = await self.user_group_repo.get_by_user_id(user_id)
        if not remaining_user_groups:
            await self.user_repository.delete(user_id)
        
        # 检查并删除孤立的群组
        remaining_group_user_groups = await self.user_group_repo.get_by_group_id(group_id)
        if not remaining_group_user_groups:
            await self.group_repository.delete(group_id)
            
    async def delete_groups_not_in_list(self, group_ids: List[int]) -> List[int]:
        if group_ids:
            try:
                await self.group_repository.delete_groups_not_in_list(group_ids)
                # 返回清理后的group_ids列表
                return await self.group_repository.get_all()
            except Exception as e:
                raise Exception(f"Error while deleting groups not in list: {e}")
            
    async def delete_users_not_in_list(self, user_ids: List[int]) -> None:
        if user_ids:
            try:
                await self.user_repository.delete_users_not_in_list(user_ids)
            except Exception as e:
                raise Exception(f"Error while deleting users not in list: {e}")
    
    async def get_user_group_by_id(self, user_group_id: int) -> Optional[UserGroup]:
        return await self.user_group_repo.get_by_id(user_group_id)
    
            
            