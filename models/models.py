from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import cfg

# 数据库连接配置（根据你的实际数据库修改，这里以 SQLite 为例）
db_path = cfg.DB_PATH
# 自动处理：如果路径里没写 sqlite:///，我们就给它加上
if not db_path.startswith("sqlite:///"):
    # 对于 Windows 绝对路径，建议使用 sqlite:/// 后跟绝对路径
    # 如果是相对路径，确保路径正确
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
else:
    SQLALCHEMY_DATABASE_URL = db_path

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # 仅针对 SQLite 需要
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 这就是你在 models/video.py 中要继承的那个 Base
Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), index=True)  # 来源标识，加索引方便过滤
    origin_id = Column(Integer, index=True)  # 原始 ID
    name = Column(String(255), index=True)  # 影片名，加索引方便搜索
    type_name = Column(String(100))  # 细分分类
    year = Column(String(20))  # 年份
    area = Column(String(50))  # 地区
    pic = Column(String(500))  # 海报图
    remarks = Column(String(255))  # 更新状态
    update_time = Column(DateTime, default=datetime.datetime.now)
    main_category = Column(String(50), index=True)  # 你打标的大类
    # 视频合集指纹字段，用于存储清洗后的核心标题
    group_title = Column(String(255), index=True)

    # 一对一关联：一个电影对应一个详情
    # uselist=False 确保是一对一关系
    detail = relationship("MovieDetail", back_populates="movie", uselist=False)


class MovieDetail(Base):
    __tablename__ = "movie_details"

    # movie_id 既是外键也是主键（因为是一对一）
    movie_id = Column(Integer, ForeignKey("movies.id"), primary_key=True)
    actor = Column(Text)  # 演员多，用 Text
    director = Column(String(255))
    content = Column(Text)  # 剧情简介
    play_url = Column(Text)  # 播放地址极长，务必用 Text 或 LongText

    # 反向关联
    movie = relationship("Movie", back_populates="detail")
