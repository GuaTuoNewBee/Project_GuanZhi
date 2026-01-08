import os
from pathlib import Path
import sys


# 获取当前运行环境的根目录
if getattr(sys, "frozen", False):
    # 打包后的 .exe 所在目录
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境所在的目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # app 基础信息
    APP_NAME = "观止(ViewStop)"
    AUTHOR = "瓜哥"
    APP_VERSION = "1.0.0"
    DB_VERSION = 1
    # 路径管理
    DB_NAME = "gz.db"
    DB_PATH = os.path.join(BASE_DIR, DB_NAME)
    QML_PATH = os.path.join(BASE_DIR, "views")
    ICONS_PATH = os.path.join(BASE_DIR, "assets", "icons")
    IMAGES_PATH = os.path.join(BASE_DIR, "assets", "images")
    # 图片缓存路径
    CACHE_POSTER_DIR = os.path.join(BASE_DIR, ".cache", "posters")

    # 资源采集控制
    USER_AGENT = f"ViewStop/{APP_VERSION} (Project_GuanZhi)"
    # 同时采集的线程数
    CRAWL_THREADS = 5
    TIMEOUT = 10  # 网络超时时间
    # 资源站配置
    RESOURCE_SOURCES = [
        {
            "id": "lz",
            "name": "量子",
            "api": "https://cj.lziapi.com/api.php/provide/vod/at/json/",
            "actived": True,
            "speed": 5,  # 1-5星评分
            "tag": "4K/极速",
            "group": "main",
        },
        {
            "id": "sn",
            "name": "索尼",
            "api": "https://suoniapi.com/api.php/provide/vod/at/json/",
            "actived": True,
            "speed": 4,
            "tag": "老牌/稳",
            "group": "main",
        },
        {
            "id": "ff",
            "name": "非凡",
            "api": "https://cj.ffzyapi.com/api.php/provide/vod/at/json/",
            "actived": True,
            "speed": 4,
            "tag": "资源全",
            "group": "main",
        },
        {
            "id": "rn",
            "name": "红牛",
            "api": "https://www.hongniuzy2.com/api.php/provide/vod/from/hnm3u8/at/json/",
            "actived": True,
            "speed": 5,
            "tag": "秒播/蓝光",
            "group": "speed",
        },
        {
            "id": "fs",
            "name": "飞速",
            "api": "https://www.feisuzyapi.com/api.php/provide/vod/at/json/",
            "actived": False,  # 示例：如果该站维护，设为False
            "speed": 3,
            "tag": "备用",
            "group": "speed",
        },
        {
            "id": "wl",
            "name": "卧龙",
            "api": "https://wolongzy.cc/api.php/provide/vod/at/json/",
            "actived": True,
            "speed": 3,
            "tag": "经典片源",
            "group": "backup",
        },
        {
            "id": "hy",
            "name": "虎牙",
            "api": "https://www.huayazy.com/api.php/provide/vod/at/json/",
            "actived": False,
            "speed": 4,
            "tag": "综合类",
            "group": "backup",
        },
        {
            "id": "kc",
            "name": "快车",
            "api": "https://caiji.kczyapi.com/api.php/provide/vod/at/json/",
            "actived": False,
            "speed": 2,
            "tag": "备用线路",
            "group": "backup",
        },
    ]
    # 统一分类映射 (处理不同站点的分类命名差异)
    # ... 其他配置 ...
    CATEGORY_MAPPING = {
        "纪录片": ["纪录片", "记录片", "纪实", "纪录", "纪录影院"],
        "动作片": ["动作片", "动作", "武侠"],
        "喜剧片": ["喜剧片", "喜剧"],
        "科幻片": ["科幻片", "科幻"],
        "恐怖片": ["恐怖片", "恐怖", "惊悚"],
        "短剧": ["短剧", "爽剧", "连载短剧", "微短剧"],
        "综艺": ["综艺", "电影解说", "解说"],
        "伦理电影": ["伦理", "伦理电影", "三级", "福利", "理论片", "情色"],
    }


cfg = Config()
