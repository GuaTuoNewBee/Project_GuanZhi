import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: brandSearchRoot
    spacing: 20
    anchors.leftMargin: 0
    anchors.rightMargin: 0

    signal searchTriggered(string text)
    signal refreshClicked

    // --- 左侧：品牌 Logo ---
    Column {
        spacing: 2
        Text {
            text: "观止"
            font.pixelSize: 60
            font.weight: Font.DemiBold
            font.letterSpacing: 4
            color: "#2C3E50"
        }
        Text {
            text: "观世界 · 止于此"
            font.pixelSize: 18
            font.letterSpacing: 2
            color: "#A0AEC0"
            font.weight: Font.Light
        }
    }

    Item {
        Layout.fillWidth: true
    }

    // --- 中间：搜索框 ---
    Rectangle {
        id: searchBar
        Layout.preferredWidth: 320
        Layout.preferredHeight: 40
        radius: 20
        color: "white"
        border.color: searchInput.activeFocus ? "#CBD5E0" : "#F0F0F0"
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 4
            spacing: 0

            TextField {
                id: searchInput
                placeholderText: "探索感兴趣的内容..."
                Layout.fillWidth: true
                background: null
                font.pixelSize: 13
                color: "#4A5568"
                verticalAlignment: TextInput.AlignVCenter

                // ✅ 核心修改 1：删除了 Timer 和 onTextChanged
                // 这样输入法选词、按空格等操作都不会误触发搜索

                // ✅ 核心修改 2：仅在按下回车键时触发
                onAccepted: {
                    brandSearchRoot.searchTriggered(text.trim());
                }
            }

            // 一键清空 (✕)
            Text {
                text: "✕"
                font.pixelSize: 12
                color: "#E2E8F0"
                visible: searchInput.text.length > 0
                padding: 10
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        searchInput.clear();
                        searchInput.forceActiveFocus();
                        // 清空时重置列表
                        brandSearchRoot.searchTriggered("");
                    }
                }
            }

            // 🔍 搜索按钮
            Rectangle {
                id: searchActionBtn
                width: 44
                height: 32
                radius: 16
                color: mouseBtn.containsMouse ? "#F7FAFC" : "transparent"

                Text {
                    anchors.centerIn: parent
                    text: "🔍"
                    font.pixelSize: 16
                    color: (searchInput.text.length > 0 || mouseBtn.containsMouse) ? "#718096" : "#CBD5E0"
                }

                MouseArea {
                    id: mouseBtn
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        // ✅ 核心修改 3：点击按钮时手动触发
                        brandSearchRoot.searchTriggered(searchInput.text.trim());
                    }
                }
            }
        }
    }

    // --- 右侧：刷新按钮 ---
    ToolButton {
        text: "↻"
        font.pixelSize: 20
        onClicked: brandSearchRoot.refreshClicked()
        background: Rectangle {
            color: parent.hovered ? "#EDF2F7" : "transparent"
            radius: 20
        }
    }
}