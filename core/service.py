import re
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import joinedload
import math
from models.models import Movie
from config import cfg


class MovieService:
    def __init__(self, session_factory):
        self.Session = session_factory

    def _get_core_title(self, title):
        """增强版清洗：去掉所有后缀、括号、年份、特殊字符"""
        if not title:
            return ""

        # 1. 保存原始备份，防止洗得太过火
        original_t = title.strip()
        t = original_t

        patterns = [
            r"[\(\[\{【（].*?[\)\]\}】）]",  # 匹配括号内容
            r"\s?第[\d一二三四五六七八九十]+[季集期].*",
            r"\s?\d{4}期|\d{4}赛季",
            r"\s?(粤语|国语|英语|4K|HD|BD|蓝光|高清|1080P|修补版).*",
            # 去掉冒号或横杠后内容
            # r"[:：-].*",
        ]

        for p in patterns:
            # 使用 re.sub 替换，并去除首尾空格
            t = re.sub(p, "", t, flags=re.IGNORECASE).strip()

        # 2. 安全检查：如果洗完之后名字没了（比如标题全是括号或全是数字）
        # 则返回原名的前 10 个字符，确保 group_title 不为空
        return t if t else original_t[:10]

    def _serialize_movie(self, movie):
        """主页面和详情页通用的序列化方法"""
        try:
            return {
                "id": movie.id,
                "name": movie.name,
                "pic": getattr(movie, "pic", ""),
                "remarks": getattr(movie, "remarks", ""),
                # 💡 修正这里：从数据库的 type_name 字段取值
                "type_name": getattr(movie, "type_name", ""),
                "year": getattr(movie, "year", ""),
                "area": getattr(movie, "area", ""),
                "group_title": getattr(movie, "group_title", ""),
                # 💡 额外：如果想让“剧情简介”在列表里也能备用，可以加上
                "des": getattr(movie.detail, "content", "") if movie.detail else "",
            }
        except Exception as e:
            print(f"❌ 序列化单条电影失败: {e}")
            return {"id": movie.id, "name": "数据解析错误"}

    def _parse_urls(self, url_str: str) -> list:
        if not url_str:
            return []

        episodes = []
        # 采集站通常用 # 分隔每一集
        parts = url_str.split("#")
        for part in parts:
            if "$" in part:
                sub = part.split("$")
                if len(sub) >= 2:
                    name = sub[0].strip()
                    url = sub[1].strip()

                    # 💡 核心过滤：只保留 m3u8，且排除掉那种跳转网页 (share)
                    url_lower = url.lower()
                    if ".m3u8" in url_lower and "/share/" not in url_lower:
                        episodes.append({"name": name, "url": url})

            elif "http" in part:  # 兜底逻辑
                url = part.strip()
                if ".m3u8" in url.lower() and "/share/" not in url.lower():
                    episodes.append({"name": "正片", "url": url})
        return episodes

    def get_by_main_category(
        self, category_name: str, page: int = 1, page_size: int = 50, **kwargs
    ):
        targets = cfg.CATEGORY_MAPPING.get(category_name, [category_name])
        offset_value = (page - 1) * page_size

        # 针对不适合聚合的分类做特殊处理
        skip_group = category_name == "伦理电影"

        with self.Session() as session:
            if skip_group:
                # --- 路径 A：直接查询（不聚合） ---
                query = session.query(Movie).filter(Movie.main_category.in_(targets))
                total_series_count = query.count()
                results = (
                    query.order_by(desc(Movie.update_time))
                    .limit(page_size)
                    .offset(offset_value)
                    .all()
                )
                # 这里的 results 只是 Movie 对象列表
                items_to_serialize = [(m, 1, m.update_time) for m in results]
            else:
                # --- 路径 B：核心聚合逻辑 ---
                total_series_count = (
                    session.query(func.count(distinct(Movie.group_title)))
                    .filter(Movie.main_category.in_(targets))
                    .scalar()
                ) or 0

                # 这里的优化点：利用子查询先锁定每一组最新的 ID
                # 这样能保证拿到的 m_obj 一定是该系列里最新更新的那一季
                subq = (
                    session.query(
                        func.max(Movie.id).label("max_id"),
                        func.count(Movie.id).label("v_count"),
                        func.max(Movie.update_time).label("latest_ts"),
                    )
                    .filter(Movie.main_category.in_(targets))
                    .group_by(Movie.group_title)
                    .subquery()
                )

                results = (
                    session.query(Movie, subq.c.v_count, subq.c.latest_ts)
                    .join(subq, Movie.id == subq.c.max_id)
                    .order_by(desc(subq.c.latest_ts))
                    .limit(page_size)
                    .offset(offset_value)
                    .all()
                )
                items_to_serialize = results

            final_list = []
            for m_obj, v_count, latest_time in items_to_serialize:
                data = self._serialize_movie(m_obj)

                # 如果是常规聚合类，重写名称和备注
                if not skip_group:
                    data["name"] = m_obj.group_title
                    data["update_time"] = latest_time
                    if v_count > 1:
                        data["remarks"] = f"更新至 {v_count} 个版本/季"

                final_list.append(data)

            # 分页逻辑
            total_pages = (
                math.ceil(total_series_count / page_size)
                if total_series_count > 0
                else 1
            )

            return {
                "items": final_list,
                "pagination": {
                    "total_records": total_series_count,
                    "total_pages": total_pages,
                    "current_page": page,
                    "page_size": page_size,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                },
            }

    def get_movie_detail(self, movie_id: int):
        """
        详情页优化：增加对播放组的去重保护
        """
        with self.Session() as session:
            movie = (
                session.query(Movie)
                .options(joinedload(Movie.detail))
                .filter(Movie.id == movie_id)
                .first()
            )
            if not movie:
                return None

            data = self._serialize_movie(movie)
            # 补全详情信息
            detail_obj = movie.detail
            data.update(
                {
                    "director": getattr(detail_obj, "director", "未知") or "未知",
                    "actor": getattr(detail_obj, "actor", "未知") or "未知",
                    "des": getattr(detail_obj, "content", "暂无简介") or "暂无简介",
                }
            )

            # 获取所有版本并解析地址
            play_groups = []
            all_versions = (
                session.query(Movie)
                .options(joinedload(Movie.detail))
                .filter(Movie.group_title == movie.group_title)
                .order_by(
                    Movie.year.desc(), Movie.id.desc()
                )  # 💡 优化：按年份和ID倒序，让最新的排在前面
                .all()
            )

            seen_urls = set()  # 💡 增加 URL 去重，防止同一站点的重复采集
            for v in all_versions:
                if v.detail and v.detail.play_url:
                    eps = self._parse_urls(v.detail.play_url)
                    if eps:
                        # 简单的防重逻辑：如果这一组的第一集 URL 已经出现过，跳过
                        if eps[0]["url"] not in seen_urls:
                            play_groups.append({"season_name": v.name, "episodes": eps})
                            seen_urls.add(eps[0]["url"])

            data["play_groups"] = play_groups
            return data

    def get_movies(self, page: int = 1, page_size: int = 50, **filters):
        offset_value = (page - 1) * page_size
        cat_name = filters.get("category_name")

        # 1. 安全获取参数
        type_filter = str(filters.get("type_name") or "")
        year_filter = str(filters.get("year") or "")
        area_filter = str(filters.get("area") or "")
        keyword = str(filters.get("keyword") or "")
        order_type = str(filters.get("order") or "time")  # 默认按时间排序

        # 逻辑判断：伦理电影和“其他”分类不进行 group_title 聚合
        skip_group = cat_name == "其他" or cat_name == "伦理电影"

        with self.Session() as session:
            conditions = []

            # --- 2. 构建过滤条件池 (conditions) ---
            if keyword:
                conditions.append(Movie.name.like(f"%{keyword}%"))

            if cat_name and cat_name != "全部":
                targets = cfg.CATEGORY_MAPPING.get(cat_name, [cat_name])
                conditions.append(Movie.main_category.in_(targets))

            if year_filter and year_filter != "全部":
                conditions.append(Movie.year.like(f"{year_filter}%"))

            if type_filter and type_filter != "全部":
                clean_type = type_filter.replace("片", "").replace("剧", "")
                conditions.append(Movie.type_name.like(f"%{clean_type}%"))

            if area_filter and area_filter != "全部":
                clean_area = area_filter.replace("中国", "").replace("其他", "其")
                conditions.append(Movie.area.like(f"%{clean_area}%"))

            # --- 3. 确定排序逻辑 (适配现有字段) ---
            order_map = {
                "time": Movie.update_time,
                "hits": Movie.id,  # 数据库无 hits，暂用 id
                "score": Movie.update_time,  # 数据库无 score，暂用时间
            }
            sort_field = order_map.get(order_type, Movie.update_time)

            # --- 4. 开始执行查询 ---
            try:
                if skip_group:
                    # --- 路径 A：不聚合 ---
                    query = session.query(Movie).filter(*conditions)
                    total_count = query.count()
                    results = (
                        query.order_by(desc(sort_field))
                        .limit(page_size)
                        .offset(offset_value)
                        .all()
                    )
                    items_to_serialize = [(m, 1, m.update_time) for m in results]
                else:
                    # --- 路径 B：聚合逻辑 ---
                    total_count = (
                        session.query(func.count(distinct(Movie.group_title)))
                        .filter(*conditions)
                        .scalar()
                        or 0
                    )

                    # 子查询：聚合每个 group_title 的度量值
                    subq = (
                        session.query(
                            func.max(Movie.id).label("max_id"),
                            func.count(Movie.id).label("v_count"),
                            func.max(Movie.update_time).label("latest_ts"),
                        )
                        .filter(*conditions)
                        .group_by(Movie.group_title)
                        .subquery()
                    )

                    # ✅ 修正语法错误：Python 使用 elif 而不是 else: order_type ==
                    if order_type == "hits":
                        final_order = desc(subq.c.max_id)
                    else:
                        final_order = desc(subq.c.latest_ts)

                    results = (
                        session.query(Movie, subq.c.v_count, subq.c.latest_ts)
                        .join(subq, Movie.id == subq.c.max_id)
                        .order_by(final_order)
                        .limit(page_size)
                        .offset(offset_value)
                        .all()
                    )
                    items_to_serialize = results

                # --- 5. 序列化并返回 ---
                final_list = []
                for m_obj, v_count, latest_time in items_to_serialize:
                    data = self._serialize_movie(m_obj)
                    if not skip_group:
                        data["name"] = m_obj.group_title
                        data["update_time"] = (
                            latest_time.strftime("%Y-%m-%d") if latest_time else ""
                        )
                        data["remarks"] = (
                            f"更新至 {v_count} 个版本"
                            if v_count > 1
                            else (data["remarks"] or "完结")
                        )
                    final_list.append(data)

                total_pages = (
                    math.ceil(total_count / page_size) if total_count > 0 else 1
                )

                return {
                    "items": final_list,
                    "pagination": {
                        "total_records": total_count,
                        "total_pages": total_pages,
                        "current_page": page,
                        "page_size": page_size,
                        "has_next": page < total_pages,
                        "has_prev": page > 1,
                    },
                }

            except Exception as e:
                print(f"❌ 数据库查询异常: {e}")
                import traceback

                traceback.print_exc()
                return {
                    "items": [],
                    "pagination": {"total_records": 0, "total_pages": 1},
                }
