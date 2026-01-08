import os
import hashlib
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt

from config import cfg


class GZImageProvider(QQuickImageProvider):
    def __init__(self):
        # 使用 Image 类型配合 QML 的 sourceSize 能达到最佳性能平衡
        super().__init__(QQuickImageProvider.Image)
        self.img_cache_dir = cfg.CACHE_POSTER_DIR
        if not os.path.exists(self.img_cache_dir):
            os.makedirs(self.img_cache_dir, exist_ok=True)

    def requestImage(self, path, *args):
        """
        ⚡ 异步加载核心：
        QML 传来的 path 可能带有刷新后缀，例如: "http://xxx.com/a.jpg?v=1"
        """
        # 1. 🔥 核心修正：剥离查询参数
        # 必须先去掉 ?v=... 部分，否则计算出的 MD5 会随 Ticket 改变而改变
        clean_path = path.split("?")[0]

        # 2. 清洗 URL（修复斜杠）并生成哈希
        url = self._clean_url(clean_path)
        if not url:
            return self._make_placeholder()

        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        local_path = os.path.join(self.img_cache_dir, f"{url_hash}.webp")

        # 3. 尝试从本地磁盘加载
        image = QImage()
        if os.path.exists(local_path):
            if image.load(local_path):
                # ✅ 成功拿到缓存图
                return image

        # 4. 如果本地没有，返回透明占位图
        # 后台下载线程完成后会发出 resultsChanged 信号，
        # 届时 QML 侧 Ticket 增加，会再次触发本方法并进入上面的成功逻辑。
        return self._make_placeholder()

    def _clean_url(self, path):
        """修复 QML 传过来的 URL 路径问题"""
        if not path:
            return ""
        url = path
        # 兼容处理 QML 自动吞掉协议斜杠的问题
        if url.startswith("https:/") and not url.startswith("https://"):
            url = url.replace("https:/", "https://", 1)
        elif url.startswith("http:/") and not url.startswith("http://"):
            url = url.replace("http:/", "http://", 1)
        return url if url.startswith("http") else ""

    def _make_placeholder(self):
        """创建一个极小的透明占位，几乎不占内存"""
        img = QImage(1, 1, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        return img
