import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: parent.width
    height: 65
    color: "#FFFFFF"

    // --- 属性与信号定义 ---
    property int sidePadding: 40
    property string activeCategory: "电影"
    
    // 💡 关键修正：必须声明此信号，父组件 GZMainWindow 才能监听到 onCategoryChanged
    signal categoryChanged(string category) 

    // 加载弹窗组件
    AboutDialog { id: aboutDialog }

    // --- 1. 底部装饰线 ---
    Rectangle {
        width: parent.width; height: 1; color: "#F1F3F5"
        anchors.bottom: parent.bottom
        z: 2 // 确保在最上层
    }

    // --- 2. 分类滚动区 ---
    Flickable {
        anchors.fill: parent
        // 💡 这里的 rightMargin 要足够大，防止分类文字滚到“关于作者”下面去
        anchors.rightMargin: 120 
        contentWidth: navRow.width + (root.sidePadding * 2)
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        
        Row {
            id: navRow
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: root.sidePadding
            spacing: 50

            Repeater {
                model: ["电影", "纪录片", "电视剧", "动漫", "综艺/解说", "体育", "伦理电影", "其他"]
                delegate: Item {
                    width: navText.implicitWidth
                    height: 40
                    
                    Text {
                        id: navText
                        text: modelData
                        anchors.centerIn: parent
                        font.pixelSize: 15
                        font.letterSpacing: 1
                        // 选中的颜色逻辑
                        color: root.activeCategory === modelData ? "#2196F3" : "#4A5568"
                        
                        Behavior on color { ColorAnimation { duration: 200 } }
                    }

                    // 选中状态的下划线
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: -12 // 调整位置贴合底线
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: root.activeCategory === modelData ? navText.width : 0
                        height: 2
                        color: "#2196F3"
                        Behavior on width { NumberAnimation { duration: 200 } }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.activeCategory = modelData;
                            // 1. 调用 Python 后端逻辑
                            GZBridge.set_main_type(modelData);
                            // 2. 💡 发送信号通知父组件（解决报错的关键）
                            root.categoryChanged(modelData);
                        }
                    }
                }
            }
        }
    }

    // --- 3. 最右侧固定文字按钮 ---
    Text {
        id: aboutBtn
        text: "关于"
        anchors.right: parent.right
        anchors.rightMargin: root.sidePadding
        anchors.verticalCenter: parent.verticalCenter
        
        font.pixelSize: 14
        font.weight: Font.Medium
        // 悬停变色逻辑
        color: aboutMouse.containsMouse ? "#2196F3" : "#94A3B8"
        
        Behavior on color { ColorAnimation { duration: 200 } }

        MouseArea {
            id: aboutMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: aboutDialog.open()
        }

        // 文字下划线装饰
        Rectangle {
            width: parent.width
            height: 1
            color: parent.color
            anchors.top: parent.bottom
            anchors.topMargin: 2
            opacity: 0.3
        }
    }
}