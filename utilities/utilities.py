from sys import platform
import time
import os
import sqlite3

from sqlalchemy import create_engine, func, or_, text
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm
from config import cfg
from models.models import Movie


class Utilities:

    @staticmethod
    def check_db_info(limit=5):
        """
        用于查看已经存在的 sqlite db 文件的数据结构和表
        """
        if not os.path.exists(cfg.DB_PATH):
            print(f"[警告] 数据库文件不存在: {cfg.DB_PATH}")
            return None
        try:
            conn = sqlite3.connect(cfg.DB_PATH)
            cursor = conn.cursor()

            # 修正 1: 获取所有表名 (使用 SQL 语句而不是 .TABLES)
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            tables = [t[0] for t in cursor.fetchall()]

            results = []
            for table in tables:
                # 修正 2: 修正 PRAGMA 拼写错误，并在表名上加引号防止特殊字符报错
                cursor.execute(f"PRAGMA table_info('{table}');")
                columns = [col[1] for col in cursor.fetchall()]

                # 修正 3: 确保 SELECT 后面有空格
                cursor.execute(f"SELECT * FROM '{table}' LIMIT {limit};")
                rows = cursor.fetchall()

                results.append({"table": table, "column": columns, "data": rows})

            cursor.close()
            conn.close()  # 别忘了关闭连接
            return results

        except Exception as e:
            print(f"[警告] 数据读取错误: {e}")
            return None

    @staticmethod
    def check_db_info_to_txt(db_info, output_file="db_info.txt"):
        """
        保存读出来的样例数据到文本文件 db_info.txt
        """
        with open(output_file, "w", encoding="utf-8") as f:
            for item in db_info:
                f.write(f"表：{item['table']}\n")
                f.write(f"字段：{', '.join(item['column'])}\n")
                f.write("-" * 20 + "数据样本 " + "-" * 20 + "\n")
                for row in item["data"]:
                    f.write(str(row) + "\n")
                f.write("\n" + "=" * 50 + "\n\n")
        return f"[信息] 数据写入 {output_file} 完成....."

    @staticmethod
    def get_category_summary():
        """
        获取目前数据库中的所有type_name类型及数量
        """
        conn = sqlite3.connect(cfg.DB_PATH)
        cursor = conn.cursor()
        # 统计所有不同的 type_name 及其数量
        cursor.execute(
            "SELECT type_name, COUNT(*) FROM movies GROUP BY type_name ORDER BY COUNT(*) DESC"
        )
        results = cursor.fetchall()
        conn.close()
        for name, count in results:
            print(f"二级分类: {name:15} | 数量: {count}")

    @staticmethod
    def get_main_category(type_name, remarks, play_url):
        """
        核心多维权重逻辑：利用链接密度(link_count)和特征词实现高精度归类
        """
        tn = str(type_name) if type_name else ""
        rm = str(remarks) if remarks else ""
        url = str(play_url) if play_url else ""

        # 计算链接密度：$ 是集与集的分隔，$$$ 是来源的分隔
        # 电影即使有3个来源，总 $ 数通常也 < 8；而电视剧一集就能贡献好几个 $
        link_count = url.count("$")

        # 1. 强特征优先判定 (成人、短剧、体育、综艺、纪录片)
        if any(k in tn for k in ["伦理", "三级", "写真", "热舞", "两性", "福利"]):
            return "成人/隐私"
        if "短剧" in tn or "爽剧" in tn:
            return "短剧"
        if any(k in tn for k in ["足球", "篮球", "体育", "赛事", "网球", "斯诺克"]):
            return "体育"
        if any(k in tn for k in ["解说", "综艺", "演唱会", "晚会", "真人秀"]):
            return "综艺/解说"
        if any(k in tn for k in ["纪录", "记录", "科普", "学习"]):
            return "纪录片"

        # 2. 电影精准拦截逻辑
        # 特征：备注含正片/高清关键词 且 链接总数很少（排除掉像 ID 1 这种伪装成电影的短剧/剧集）
        movie_signals = ["正片", "HD", "BD", "4K", "超清", "蓝光", "1080P", "720P"]
        if any(k in rm.upper() for k in movie_signals):
            if link_count <= 5:  # 绝大多数电影（含多来源）都在此范围
                return "电影"

        # 3. 动漫与动画判定 (区分剧场版与连载版)
        if "动漫" in tn or "动画" in tn:
            # 如果动漫备注是高清且链接很少，判定为动漫电影（剧场版）
            if any(k in rm.upper() for k in movie_signals) and link_count <= 3:
                return "电影"
            return "动漫"

        # 4. 电视剧判定 (基于备注关键词和超长链接列表)
        series_signals = ["集", "期", "连载", "完结", "更新至"]
        # 这里的 link_count > 5 是关键，像你样本中 ID 1, 2 这种长链接会直接命中
        if any(k in rm for k in series_signals) or link_count > 5:
            return "电视剧"

        # 5. 纯题材判定 (兜底逻辑)
        if "剧" in tn and "电影" not in tn:
            return "电视剧"

        movie_genres = [
            "剧情",
            "动作",
            "喜剧",
            "恐怖",
            "爱情",
            "科幻",
            "战争",
            "惊悚",
            "电影",
            "片",
        ]
        if any(k in tn for k in movie_genres):
            return "电影"

        return "其他"

    @staticmethod
    def run_classification():
        """
        归类数据并添加main_catatory字段
        """
        conn = sqlite3.connect(cfg.DB_PATH)
        cursor = conn.cursor()

        # 1. 新增 main_category 字段
        try:
            cursor.execute("ALTER TABLE movies ADD COLUMN main_category TEXT")
            print("[OK] 已新增 main_category 字段")
        except sqlite3.OperationalError:
            print("[Info] main_category 字段已存在，准备重新计算")

        # 2. 一次性提取所有必要数据 (使用 JOIN 关联详情表)
        print("[Step 1/3] 正在读取全库数据并计算分类...")
        query = """
        SELECT m.id, m.type_name, m.remarks, d.play_url 
        FROM movies m
        LEFT JOIN movie_details d ON m.id = d.movie_id
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # 3. 内存处理数据
        updates = []
        for row in tqdm(rows, desc="计算中"):
            m_id, t_name, remarks, play_url = row
            cat = Utilities.get_main_category(t_name, remarks, play_url)
            updates.append((cat, m_id))

        # 4. 开启事务批量写入
        print(f"[Step 2/3] 正在写入数据库 (共 {len(updates)} 条)...")
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.executemany(
                "UPDATE movies SET main_category = ? WHERE id = ?", updates
            )
            conn.commit()
            print("[Step 3/3] 写入成功！")
        except Exception as e:
            conn.rollback()
            print(f"[Error] 写入失败: {e}")
        finally:
            conn.close()

    @staticmethod
    def check_results():
        """
        用户查看归类添加main_category字段后的数据库
        """
        conn = sqlite3.connect(cfg.DB_PATH)
        cursor = conn.cursor()

        # 统计每个大类的分布情况
        cursor.execute(
            "SELECT main_category, COUNT(*) FROM movies GROUP BY main_category ORDER BY COUNT(*) DESC"
        )
        rows = cursor.fetchall()

        print("\n==== 🏆 数据库分类打标结果统计 ====")
        print(f"{'大分类名称':<15} | {'数据量':<10}")
        print("-" * 30)
        for cat, count in rows:
            print(f"{str(cat):<15} | {count:<10}")

        conn.close()

    @staticmethod
    def cleanup_database(keywords=None, categories=None):
        """
        通用清理工具：根据传入的关键词列表或分类列表删除数据
        :param keywords: 列表类型，匹配 name 或 remarks 字段 (模糊匹配)
        :param categories: 列表类型，匹配 main_category 或 type_name 字段 (精确匹配)
        """
        # 参数归一化：确保即使传入单个字符串也能处理成列表
        keywords = [keywords] if isinstance(keywords, str) else (keywords or [])
        categories = [categories] if isinstance(categories, str) else (categories or [])

        if not keywords and not categories:
            print("⚠️ 未提供任何关键词或分类参数，取消操作。")
            return

        DB_PATH = cfg.DB_PATH
        if not str(DB_PATH).startswith("sqlite:///"):
            engine = create_engine(f"sqlite:///{DB_PATH}")
        else:
            engine = create_engine(DB_PATH)

        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            print(f"🔍 正在根据参数扫描数据库...")
            print(f"   - 关键词匹配: {keywords}")
            print(f"   - 分类精确匹配: {categories}")

            filters = []

            # 1. 处理关键词逻辑 (模糊匹配标题或备注)
            for kw in keywords:
                filters.append(Movie.name.like(f"%{kw}%"))
                filters.append(Movie.remarks.like(f"%{kw}%"))

            # 2. 处理分类逻辑 (精确匹配一级或二级分类)
            if categories:
                filters.append(Movie.type_name.in_(categories))
                filters.append(Movie.main_category.in_(categories))

            # 3. 执行查询
            query = session.query(Movie).filter(or_(*filters))
            count = query.count()

            if count == 0:
                print("✨ 数据库中未发现符合上述条件的记录。")
                return

            print(f"⚠️ 匹配到 {count} 条相关记录。")

            # 抽样显示前 8 条
            samples = query.limit(8).all()
            print("\n--- 抽样预览 ---")
            for s in samples:
                print(
                    f"ID: {s.id} | 名称: {s.name[:25]} | 类型: {s.main_category}/{s.type_name} | 备注: {s.remarks}"
                )
            print("----------------\n")

            confirm = input(f"确认要从数据库永久删除这 {count} 条数据吗？(y/n): ")
            if confirm.lower() == "y":
                query.delete(synchronize_session=False)
                session.commit()
                print(f"✅ 清理完成！已删除 {count} 条记录。")
            else:
                print("❌ 操作已取消。")

        except Exception as e:
            session.rollback()
            print(f"❌ 清理出错: {e}")
        finally:
            session.close()

    @staticmethod
    def initialize_movie_groups(session_factory, movie_service):
        """
        全局一次性合集初始化（全库安全版）
        """
        session = session_factory()
        try:
            # 1. 统计总量（用于显示真实进度）
            total_pending = (
                session.query(Movie)
                .filter(or_(Movie.group_title == None, Movie.group_title == ""))
                .count()
            )

            if total_pending == 0:
                print("✨ 数据库已是最新状态，无需初始化。")
                return

            print(f"🚀 准备处理 {total_pending} 条未标注数据...")

            batch_size = 500  # 减小批次，每处理 500 条 commit 一次，降低崩溃风险
            processed_count = 0

            while True:
                # 每次取最新的 500 条未处理数据
                batch_movies = (
                    session.query(Movie)
                    .filter(or_(Movie.group_title == None, Movie.group_title == ""))
                    .limit(batch_size)
                    .all()
                )

                if not batch_movies:
                    break

                for m in batch_movies:
                    if not m.name:
                        m.group_title = "未知名称"
                        continue

                    try:
                        # 执行核心清洗逻辑
                        cleaned_name = movie_service._get_core_title(m.name)
                        # 如果清洗后变空了（极端情况），保留原名
                        m.group_title = cleaned_name if cleaned_name else m.name.strip()
                    except Exception as e:
                        print(f"❌ 处理 ID:{m.id} 名:{m.name} 时出错: {e}")
                        m.group_title = m.name.strip()  # 出错则保留原名，确保脚本不中断

                session.commit()  # 每一批次提交一次数据库
                processed_count += len(batch_movies)
                print(f"⏳ 进度: {processed_count}/{total_pending} (当前批次已入库)")

            print(f"✅ 全局合集指纹标注完成！共处理 {processed_count} 条数据。")

        except Exception as e:
            session.rollback()
            print(f"❌ 关键性错误: {e}")
        finally:
            session.close()

    @staticmethod
    def add_group_title_column(engine):
        with engine.connect() as conn:
            try:
                # 检查字段是否存在
                conn.execute(text("SELECT group_title FROM movies LIMIT 1"))
                print("✅ group_title 字段已存在。")
            except Exception:
                print("⚠️ 正在向数据库添加 group_title 字段...")
                # 执行 SQL 添加字段
                conn.execute(
                    text("ALTER TABLE movies ADD COLUMN group_title VARCHAR(255)")
                )
                # 创建索引，提升后续合集查询速度
                conn.execute(
                    text("CREATE INDEX ix_movies_group_title ON movies (group_title)")
                )
                conn.commit()
                print("✅ 字段及索引添加成功！")

    @staticmethod
    def check_group_results(SessionFactory):
        session = SessionFactory()
        try:
            from sqlalchemy import func

            print("\n--- 📊 合集效果 Top 10 预览 ---")
            # 统计每个 group_title 下有多少个版本/季度
            results = (
                session.query(
                    Movie.group_title,
                    func.count(Movie.id).label("total_versions"),
                    func.group_concat(Movie.name).label("all_names"),
                )
                .group_by(Movie.group_title)
                .order_by(func.count(Movie.id).desc())
                .limit(10)
                .all()
            )

            for group_title, count, names in results:
                # names 是所有原始名称拼接的字符串，我们只取前两个展示
                name_list = names.split(",")[:2]
                print(f"核心标题: 【{group_title}】")
                print(f"  └─ 合并了 {count} 条数据 (如: {name_list}...)")
                print("-" * 30)

        finally:
            session.close()

    @staticmethod
    def fix_short_groups(session_factory):
        """
        修正逻辑：如果 group_title 太短（小于2个字符）或是已知的误伤关键词，
        则恢复为原始名称，防止误合并。
        """
        session = session_factory()
        try:
            # 1. 找出那些被误合并为 "RE" 或者长度太短的标题
            # 你可以根据预览结果把 'RE' 加入黑名单
            bad_titles = ["RE", "re", "P", "A", "HD", "4K", "TS"]

            query = session.query(Movie).filter(
                or_(
                    Movie.group_title.in_(bad_titles),
                    func.length(Movie.group_title)
                    <= 1,  # 长度只有1位的标题通常也是误伤
                )
            )

            count = query.count()
            if count > 0:
                print(f"🛠️ 正在修复 {count} 条误伤数据...")
                for m in query.all():
                    # 恢复为原始名称，让它们独立显示，不参与合并
                    m.group_title = m.name.strip()

                session.commit()
                print("✅ 修复完成。")
            else:
                print("✨ 未发现明显误伤。")
        finally:
            session.close()

    @staticmethod
    def debug_aggregation_issue(SessionFactory, category_name="电视剧"):
        session = SessionFactory()
        try:
            print(f"\n🔍 开始针对【{category_name}】大类进行深度体检...")
            start_time = time.time()

            # 1. 测试基础过滤速度（检查 main_category 索引）
            t0 = time.time()
            count = (
                session.query(Movie)
                .filter(Movie.main_category == category_name)
                .count()
            )
            print(f"  - 基础过滤: 找到 {count} 条数据，耗时: {time.time()-t0:.4f}s")

            # 2. 采样检查：为什么没合拢？
            # 找出一个你应该觉得该合拢但没合拢的例子
            print(f"\n  - 采样检查（随机抽取 5 组 group_title）:")
            samples = (
                session.query(Movie.group_title, func.count(Movie.id))
                .filter(Movie.main_category == category_name)
                .group_by(Movie.group_title)
                .having(func.count(Movie.id) > 1)
                .limit(5)
                .all()
            )

            for gt, c in samples:
                print(f"    核心标题:【{gt}】| 库中实际聚合数量: {c}")

            # 3. 性能杀手检测：检查索引情况
            print("\n  - 数据库索引状态检测:")
            result = session.execute(text("PRAGMA index_list('movies')")).fetchall()
            for idx in result:
                print(f"    找到索引: {idx[1]}")

            print(f"\n⏱️ 总诊断耗时: {time.time() - start_time:.4f}s")

        finally:
            session.close()

    @staticmethod
    def setup_hardware_acceleration():
        """
        跨平台通用逻辑：自动识别并强制系统优先调用独立显卡（高性能模式）。
        """
        # --- 1. 针对主流显卡厂家的通用引导变量 ---
        # 即使不知道具体型号，这些变量也会告诉驱动：该应用需要“高性能”

        # 针对 NVIDIA: 强制开启 Prime 渲染卸载（双显卡切换核心变量）
        os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
        os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"

        # 针对 Windows 通用: 告诉 D3D 运行时和驱动程序偏好高性能适配器
        # 这对于 AMD 和 NVIDIA 的移动端/桌面端双显卡都有效
        os.environ["SHAPER_FORCE_HIGH_PERFORMANCE"] = "1"

        # --- 2. 强制 Qt RHI 拒绝“省电”模式 ---
        # 0 表示关闭软件渲染，强制寻找硬件加速适配器
        os.environ["QSG_RHI_PREFER_SOFTWARE_RENDERER"] = "0"

        # --- 3. 根据系统环境锁定最强渲染后端 ---
        current_os = platform.system()

        if current_os == "Windows":
            # Windows 下 D3D11 在枚举硬件适配器时对“高性能”识别最准确
            # 它会自动通过 DXGI 分数选择显存更大、核心更多的显卡
            os.environ["QSG_RHI_BACKEND"] = "d3d11"
        elif current_os == "Darwin":  # macOS
            # macOS 默认会自动处理独显/核显切换 (Metal 后端)
            os.environ["QSG_RHI_BACKEND"] = "metal"
        elif current_os == "Linux":
            # Linux 优先使用 Vulkan，它对独显的调用权优于 OpenGL
            os.environ["QSG_RHI_BACKEND"] = "vulkan"

        # --- 4. 启用渲染流水线优化 ---
        # 开启多线程渲染循环，确保图形指令能并发发送给高性能 GPU
        os.environ["QSG_RENDER_LOOP"] = "threaded"

        # --- 5. 调试监控 (建议开发阶段开启) ---
        # 开启此项后，控制台会打印出具体选中的显卡型号
        os.environ["QSG_INFO"] = "1"

        print(
            f"🛠️ [硬件加速] 已完成通用引导配置，后端：{os.environ.get('QSG_RHI_BACKEND')}"
        )
