import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

RowLayout {
    id: root
    spacing: 6 // 按钮之间的紧凑间距
    
    // 💡 重点 1：确保 RowLayout 填满父级给它的空间
    // 这样它内部的居中逻辑才能生效
    anchors.fill: parent 

    signal prevPage
    signal nextPage

    property int currentPage: (typeof GZBridge !== "undefined" && GZBridge.currentPage) ? GZBridge.currentPage : 1
    property int totalPages: (typeof GZBridge !== "undefined" && GZBridge.totalPages) ? GZBridge.totalPages : 1
    property bool hasNext: (typeof GZBridge !== "undefined" && GZBridge.hasNextPage) ? GZBridge.hasNextPage : false

    // --- 按钮样式模板 ---
    component PagerButton: Button {
        id: control
        implicitWidth: text.length > 3 ? 64 : 54
        implicitHeight: 32
        Layout.alignment: Qt.AlignVCenter 
        hoverEnabled: true
        padding: 0
        
        contentItem: Item {
            anchors.fill: parent
            Text {
                text: control.text
                font.pixelSize: 13
                color: !control.enabled ? "#DCDFE6" : (control.hovered ? "#2196F3" : "#606266")
                anchors.centerIn: parent
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
        background: Rectangle { color: "transparent" }
    }

    // --- 核心布局逻辑 ---

    // 💡 重点 2：左侧“弹簧”
    // 占用左侧所有剩余空间，把按钮往中间推
    Item { Layout.fillWidth: true }

    PagerButton {
        text: "[首页]"
        enabled: root.currentPage > 1
        onClicked: GZBridge.load_page(1)
    }

    PagerButton {
        text: "上一页"
        enabled: root.currentPage > 1
        onClicked: GZBridge.load_page(root.currentPage - 1)
    }

    Rectangle {
        Layout.preferredWidth: 90
        Layout.preferredHeight: 30
        Layout.alignment: Qt.AlignVCenter
        color: "#F5F7FA"
        radius: 4
        Text {
            anchors.centerIn: parent
            text: root.currentPage + " / " + root.totalPages
            font.pixelSize: 12
            font.family: "Consolas"
            color: "#303133"
            font.bold: true
        }
    }

    PagerButton {
        text: "下一页"
        enabled: root.hasNext
        onClicked: GZBridge.load_page(root.currentPage + 1)
    }

    PagerButton {
        text: "[尾页]"
        enabled: root.currentPage < root.totalPages
        onClicked: GZBridge.load_page(root.totalPages)
    }

    // 💡 重点 3：右侧“弹簧”
    // 占用右侧所有剩余空间，把按钮往中间推
    Item { Layout.fillWidth: true }
}