import os
import subprocess
import sys
import shutil


def generate_resources():
    """打包前自动更新资源文件，确保图标和组件全部进入二进制包"""
    print("🔎 正在全自动扫描资源文件...")
    search_dirs = ["views", "assets"]
    extensions = (".qml", ".png", ".ico", ".jpg", ".svg", ".js")
    qrc_lines = ["<RCC>", '    <qresource prefix="/">']

    for folder in search_dirs:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(extensions):
                        # 规范路径斜杠，防止 Windows 下路径识别错误
                        full_path = os.path.join(root, file).replace("\\", "/")
                        qrc_lines.append(f"        <file>{full_path}</file>")

    # 扫描根目录 QML
    for f in os.listdir("."):
        if f.endswith(".qml"):
            qrc_lines.append(f"        <file>{f}</file>")

    qrc_lines.extend(["    </qresource>", "</RCC>"])

    with open("resources.qrc", "w", encoding="utf-8") as f:
        f.write("\n".join(qrc_lines))

    print("⚙️ 正在执行 pyside6-rcc 转换...")
    # 强制重新生成，确保 rc_resources.py 是最新的
    subprocess.run(
        ["pyside6-rcc", "resources.qrc", "-o", "rc_resources.py"], check=True
    )
    print(
        f"✅ rc_resources.py 已生成 (大小: {os.path.getsize('rc_resources.py') / 1024:.2f} KB)"
    )


def final_build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    app_name = "ViewStop"

    # --- 第一步：更新资源 ---
    try:
        generate_resources()
    except Exception as e:
        print(f"❌ 资源生成失败: {e}")
        return

    # --- 第二步：清理旧文件 ---
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # --- 第三步：执行打包 ---
    # 修改说明：
    # 1. 移除了 --noconsole 以启用 print 输出
    # 2. 增加了 --collect-all 以修复电影播放问题
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        # "--console",  # ✨ 开启控制台，查看运行报错
        "--clean",
        f"--name={app_name}",
        # ✨ 解决电影播放问题的核心：强制收集多媒体和网络库的所有插件
        "--collect-all",
        "PySide6.QtMultimedia",
        "--collect-all",
        "PySide6.QtNetwork",
        "--exclude-module",
        "unittest",
        "--exclude-module",
        "test",
    ]

    if os.path.exists("assets/icons/logo.ico"):
        command.extend(["--icon", "assets/icons/logo.ico"])

    command.append("gz.py")

    print(f"🚀 正在调用 PyInstaller 进行封包 (调试模式)...")
    try:
        subprocess.check_call(command)

        # --- 第四步：手动搬运外部资源 (动静分离) ---
        dist_exe_path = os.path.join("dist", app_name)

        # 搬运 .cache (海报)
        target_cache = os.path.join(dist_exe_path, ".cache")
        if os.path.exists(".cache"):
            shutil.copytree(".cache", target_cache)
            print("🚚 已搬运海报库 (.cache)")

        # 搬运数据库
        if os.path.exists("data.db"):
            shutil.copy("data.db", os.path.join(dist_exe_path, "data.db"))
            print("📂 已搬运数据库 (data.db)")

        print("\n" + "★" * 30)
        print("✅ 打包圆满完成！")
        print(f"📁 请运行此文件查看调试信息: dist/{app_name}/{app_name}.exe")
        print("★" * 30)

    except Exception as e:
        print(f"❌ 打包过程中断: {e}")


if __name__ == "__main__":
    final_build()
