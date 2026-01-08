import hashlib
import os
import threading
import time
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer
from PySide6.QtGui import QImage
import requests
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import cfg


class GZBridge(QObject):
    resultsChanged = Signal()
    currentPageChanged = Signal()
    totalPagesChanged = Signal()
    hasNextPageChanged = Signal()
    movieDetailChanged = Signal()

    def __init__(self, movie_service):
        super().__init__()
        self.service = movie_service
        self._results = []
        self._currentPage = 1
        self._totalPages = 1
        self._hasNextPage = False
        self._movieDetail = {}

        self._query_params = {
            "category_name": "电影",
            "type_name": "全部",
            "area": "全部",
            "year": "全部",
            "order": "time",
            "keyword": "",
        }

    # --- 1. 核心加载逻辑（异步） ---
    def _exec_load_logic(self, page_num):
        """后台线程：执行数据库/网络查询"""
        try:
            request_args = {
                k: v for k, v in self._query_params.items() if v != "全部" and v != ""
            }
            response = self.service.get_movies(page=page_num, **request_args)

            if response:
                self._results = response.get("items", [])
                pagination = response.get("pagination", {})
                self._totalPages = pagination.get("total_pages", 1)
                self._hasNextPage = pagination.get("has_next", False)

                # 💡 关键：数据回来后，主线程发信号刷新 UI
                self.resultsChanged.emit()
                self.currentPageChanged.emit()
                self.totalPagesChanged.emit()
                self.hasNextPageChanged.emit()

                # 💡 关键优化：UI 刷新后，后台静默下载这一页的海报（不卡顿）
                if self._results:
                    threading.Thread(
                        target=self._download_posters,
                        args=(self._results.copy(),),
                        daemon=True,
                    ).start()

                print(f"✅ 数据加载完成，已启动海报后台下载任务")
        except Exception as e:
            print(f"❌ 异步加载失败: {e}")

    def _download_posters(self, items):
        """后台线程：批量下载并保存海报到缓存目录"""
        downloaded_count = 0  # 💡 记录本次新下载成功的数量

        for item in items:
            url = item.get("pic")
            if not url or not url.startswith("http"):
                continue

            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
            local_path = os.path.join(cfg.CACHE_POSTER_DIR, f"{url_hash}.webp")

            if not os.path.exists(local_path):
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(url, headers=headers, timeout=5, verify=False)
                    if resp.status_code == 200:
                        img = QImage()
                        if img.loadFromData(resp.content):
                            img.save(local_path, "WEBP")
                            downloaded_count += 1

                            # 💡 核心逻辑：每下载成功 3 张图，就通知一次 UI 刷新
                            # 这样你不用翻页，图片也会在当前页面“一张接一张”地跳出来
                            if downloaded_count % 3 == 0:
                                self.resultsChanged.emit()

                    # 给 CPU 留一点缝隙，防止下载太猛卡住主界面渲染
                    time.sleep(0.01)
                except:
                    continue

        # 💡 循环结束后，如果还有剩下的（不满3张的），最后补发一次信号
        if downloaded_count > 0:
            self.resultsChanged.emit()
            print(f"🔔 下载任务结束，共点亮 {downloaded_count} 张新海报")

    # --- 2. 详情处理逻辑（异步化） ---
    @Slot(int, "QVariant")
    def get_detail(self, movie_id, basic_info):
        """异步获取详情，防止点击海报时界面卡死"""
        # 先存基础信息
        self._movieDetail = dict(basic_info) if basic_info else {}
        # 开线程查深度详情
        threading.Thread(
            target=self._exec_detail_logic, args=(movie_id,), daemon=True
        ).start()

    def _exec_detail_logic(self, movie_id):
        """后台查详情"""
        try:
            detail = self.service.get_movie_detail(movie_id)
            if detail:
                detail["play_groups"] = self._filter_invalid_groups(
                    detail.get("play_groups", [])
                )
                self._movieDetail.update(detail)
                self.movieDetailChanged.emit()
        except Exception as e:
            print(f"❌ 详情加载失败: {e}")

    # --- 3. 槽函数与属性 ---
    @Slot()
    def init_first_page(self):
        """首屏初始化"""
        self.load_page(1)

    @Slot(int)
    def load_page(self, page_num=1):
        """异步请求指定页"""
        self._currentPage = page_num
        thr = threading.Thread(
            target=self._exec_load_logic, args=(page_num,), daemon=True
        )
        thr.start()

    @Slot(str, str)
    def set_filter(self, key, value):
        key_map = {"main_category": "category_name"}
        real_key = key_map.get(key, key)
        if real_key in self._query_params:
            self._query_params[real_key] = value
            if real_key == "category_name":
                # 重置逻辑
                for k in ["keyword", "type_name", "area", "year"]:
                    self._query_params[k] = "" if k == "keyword" else "全部"
            self.load_page(1)

    @Slot(str)
    def search(self, keyword):
        self._query_params["keyword"] = keyword.strip()
        self.load_page(1)

    @Slot(str)
    def set_main_type(self, cat_name):
        self._query_params["category_name"] = cat_name
        # 💡 使用 QTimer 确保 QML 的点击动画先跑完，不被 Python 逻辑阻塞
        QTimer.singleShot(1, lambda: self.load_page(1))

    # --- 属性绑定 ---
    @Property(list, notify=resultsChanged)
    def results(self):
        return self._results

    @Property(int, notify=currentPageChanged)
    def currentPage(self):
        return self._currentPage

    @Property(int, notify=totalPagesChanged)
    def totalPages(self):
        return self._totalPages

    @Property(bool, notify=hasNextPageChanged)
    def hasNextPage(self):
        return self._hasNextPage

    @Property("QVariant", notify=movieDetailChanged)
    def movieDetail(self):
        return self._movieDetail

    def _filter_invalid_groups(self, groups):
        valid = []
        for g in groups:
            name = g.get("season_name", "")
            if not any(x in name for x in ["解说", "预告", "短视频"]) and g.get(
                "episodes"
            ):
                valid.append(g)
        return valid
