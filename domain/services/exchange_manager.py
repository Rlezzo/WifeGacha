import asyncio

class ExchangeManager:
    def __init__(self):
        self.active_exchanges = {}
        self.lock = asyncio.Lock()

    async def add_exchange(self, user_id, target_id, group_id):
        async with self.lock:
            if group_id not in self.active_exchanges:
                self.active_exchanges[group_id] = {}
            self.active_exchanges[group_id][user_id] = target_id

    async def remove_exchange(self, user_id, group_id):
        async with self.lock:
            if group_id in self.active_exchanges:
                if user_id in self.active_exchanges[group_id]:
                    del self.active_exchanges[group_id][user_id]
                # 如果该群的交换请求集合为空，则删除该群的记录
                if not self.active_exchanges[group_id]:
                    del self.active_exchanges[group_id]

    async def is_exchange_active(self, user_id, target_id, group_id):
        async with self.lock:
            group_exchanges = self.active_exchanges.get(group_id, {})
            for initiator, target in group_exchanges.items():
                if user_id in (initiator, target) or target_id in (initiator, target):
                    return True
            return False

    async def has_active_exchanges_in_group(self, group_id):
        async with self.lock:
            # 检查特定群是否有交易请求
            return bool(self.active_exchanges.get(group_id, {}))

    async def get_initiator_if_target(self, target_id, group_id):
        async with self.lock:
            # 检查给定ID是否是任何一个交换请求的被申请者，如果是则返回申请者ID，否则返回None
            group_exchanges = self.active_exchanges.get(group_id, {})
            for initiator, target in group_exchanges.items():
                if target == target_id:
                    return initiator
            return None