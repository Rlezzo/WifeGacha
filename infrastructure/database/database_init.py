from infrastructure.database.orm.base import Base
from infrastructure.database.orm import *  # 确保所有模型类被加载
from .connection import async_engine  # 确认连接是异步的create_async_engine

async def init_db():
    async with async_engine.begin() as conn:

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
