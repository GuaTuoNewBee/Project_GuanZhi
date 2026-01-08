import os
import subprocess


def auto_make_rc():
    # 1. 设置需要扫描的文件夹和文件类型
    search_dirs = ["views", "assets"]
    extensions = (".qml", ".png", ".ico", ".jpg", ".svg", ".js")

    qrc_lines = ["<RCC>", '    <qresource prefix="/">']

    print("🔎 正在全自动扫描文件...")

    for folder in search_dirs:
        if not os.path.exists(folder):
            continue

        # os.walk 会递归进入所有子目录（如 views/components）
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(extensions):
                    # 关键修复：确保只添加文件，并规范斜杠
                    full_path = os.path.join(root, file).replace("\\", "/")
                    qrc_lines.append(f"        <file>{full_path}</file>")
                    print(f"  + 已添加: {full_path}")

    # 同时也扫一眼根目录下有没有漏掉的 qml
    for f in os.listdir("."):
        if f.endswith(".qml"):
            qrc_lines.append(f"        <file>{f}</file>")

    qrc_lines.extend(["    </qresource>", "</RCC>"])

    # 2. 写入 qrc 文件
    with open("resources.qrc", "w", encoding="utf-8") as f:
        f.write("\n".join(qrc_lines))

    # 3. 强制转换
    print("⚙️ 正在转换二进制资源...")
    subprocess.run(["pyside6-rcc", "resources.qrc", "-o", "rc_resources.py"])
    print("✅ 全部搞定！现在 Pager.qml 和图标都在 rc_resources.py 里了。")


if __name__ == "__main__":
    auto_make_rc()
