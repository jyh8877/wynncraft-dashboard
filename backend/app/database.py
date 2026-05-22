"""数据库引擎与表初始化"""

from sqlmodel import SQLModel, create_engine

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """创建所有未存在的表"""
    SQLModel.metadata.create_all(engine)
