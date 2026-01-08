import sys
import os

# 1. 确保名称与生成的 .py 文件一致
try:
    import rc_resources
except ImportError:
    print("⚠️ 警告: 未找到资源模块 rc_resources，请先运行 pyside6-rcc")

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

# 💡 强制设置 QML 样式
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"


def main():
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("GuanZhi")
    app.setApplicationName("ViewStop")

    # --- 1. 图标路径 ---
    # 如果 logo.ico 已被扫入 qrc，直接用 qrc:/ 加载
    app.setWindowIcon(QIcon("qrc:/assets/icons/logo.ico"))

    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "GuaTuoNewBee.GuanZhi.ViewStop.1.0.1"
        )

    # --- 2. 延迟导入业务逻辑 ---
    from core.service import MovieService
    from controller.bridge import GZBridge
    from controller.provider import GZImageProvider
    from models.models import SessionLocal

    movie_service = MovieService(SessionLocal)
    bridge = GZBridge(movie_service)

    # --- 3. 引擎配置 ---
    engine = QQmlApplicationEngine()

    # 注意：ImageProvider 内部处理海报时，依然可以使用物理路径读取 .cache 文件夹
    engine.addImageProvider("poster", GZImageProvider())
    engine.rootContext().setContextProperty("GZBridge", bridge)

    # --- 4. 加载主界面 ---
    # ✨ 关键：不要用 os.path.exists 检查虚拟路径
    # 直接使用 qrc:/ 协议加载。
    # 路径必须与 resources.qrc 中定义的 <file> 标签内容一致
    # 修改第 52 行左右：
    engine.load("qrc:/views/GZMainWindow.qml")

    # --- 5. 错误检查 ---
    if not engine.rootObjects():
        print("❌ QML 加载失败！")
        print(
            "💡 请检查：1. 是否运行了 pyside6-rcc 2. qrc 路径是否包含 GZMainWindow.qml"
        )
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
