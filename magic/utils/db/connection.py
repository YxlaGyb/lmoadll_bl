# -*- coding: utf-8 -*-
"""SQLAlchemy 数据库连接模块"""
from quart import g
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from magic.utils.TomlConfig import GLOBAL_CONFIG, load_global_config

load_global_config()
_db = GLOBAL_CONFIG.get("db", {})
URL_TEMPLATES = {
    "sqlite": "sqlite:///{sql_sqlite_path}",
    "postgresql": "postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
    "mysql": "mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
}

def build_url(db_type, **cfg) -> str:
    """构建连接字符串，强制类型转换以兼容配置对象"""
    db_str = str(db_type).lower()
    if db_str not in URL_TEMPLATES:
        raise ValueError(f"Unsupported DB: {db_str}")
    return URL_TEMPLATES[db_str].format(**cfg)

DATABASE_URL = build_url(
    str(_db.get("SQLNAME", "postgresql")),
    db_user=_db.get("PGSQLUSER", "postgres"),
    db_password=_db.get("PGSQLPWD", "postgres"),
    db_host=_db.get("PGSQLHOST", "localhost"),
    db_port=_db.get("PGSQLPORT", 5432),
    db_name=_db.get("PGSQL_DB", "postgres")
)
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,   # 自动检测失效连接
    pool_recycle=3600,    # 防止数据库主动断开长连接
    pool_size=10,         # 连接池基础大小
    max_overflow=20       # 允许的最大溢出连接数
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

def init_db():
    """初始化数据库，创建所有表结构"""
    print("正在初始化数据库...")
    # Base.metadata.create_all(bind=engine)
    print("数据库初始化完成！")

def get_db():
    """获取数据库会话"""
    if "db" not in g: 
        g.db = SessionLocal()
    return g.db

def close_db(e=None):
    """关闭数据库会话"""
    db = g.pop("db", None)
    if db: 
        db.close()

def verify_db_connection(db_type: str, **config) -> tuple[bool, str | None]:
    """验证工具：用于后台管理界面测试连接"""
    try:
        test_engine = create_engine(build_url(db_type, **config))
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)
