import os
from infrastructure.database.orm import *  # 确保所有模型类被加载
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

# 获取当前文件的目录
current_directory = os.path.dirname(os.path.abspath(__file__))

# 生成数据库文件路径
database_path = os.path.join(current_directory, 'wife.db')

# 创建数据库引擎
DATABASE_URL = f'sqlite+aiosqlite:///{database_path}'
async_engine = create_async_engine(DATABASE_URL, echo=False)

# 启用 SQLite 外键约束
@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# 创建一个全局的session工厂
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=True
)

async def close_engine():
    await async_engine.dispose()