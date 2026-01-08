import os

# 定义资源根目录
qrc_content = '<RCC>\n    <qresource prefix="/">\n'

# 需要打包的文件夹白名单
resource_dirs = ["views", "components"]  # 填入你放 QML 的文件夹
# 需要打包的单个文件
root_files = ["GZMainWindow.qml", "MoviesWindow.qml"]

# 1. 处理根目录文件
for f in root_files:
    if os.path.exists(f):
        qrc_content += f"        <file>{f}</file>\n"

# 2. 递归扫描文件夹
for d in resource_dirs:
    for root, dirs, files in os.walk(d):
        for file in files:
            # 只包含界面相关文件，排除图片（海报我们说好外置的）
            if file.endswith((".qml", ".js", ".conf", ".qs")):
                path = os.path.join(root, file).replace("\\", "/")
                qrc_content += f"        <file>{path}</file>\n"

qrc_content += "    </qresource>\n</RCC>"

with open("resources.qrc", "w", encoding="utf-8") as f:
    f.write(qrc_content)

print("✅ resources.qrc 已自动生成，包含所有子目录 QML！")
