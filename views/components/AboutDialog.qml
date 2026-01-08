import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: aboutDialog
    
    // 1. 强制居中并给定明确宽度
    anchors.centerIn: parent
    width: 420
    
    // 2. 💡 终极招式：手动指定高度，确保它一定能包住内容
    // 我们让对话框高度 = 布局高度 + 上下内边距 + 按钮预留位
    height: mainLayout.height + 80
    
    modal: true
    focus: true
    
    // 清空默认背景，我们自己画，防止它不随内容变高
    background: Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        radius: 16
        border.color: "#f0f0f0"
        
        // 增加投影，增强层级感
        Rectangle {
            anchors.fill: parent
            radius: 16
            color: "transparent"
            border.color: "#10000000"
            border.width: 1
        }
    }

    // 禁用默认的 header 和 footer，因为它们会干扰高度计算
    header: Item { height: 0 }
    footer: Item { height: 0 }

    // 3. 核心布局：使用简单的 Column，手动管理位置
    Column {
        id: mainLayout
        width: parent.width - 48 // 减去左右 padding
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 30
        spacing: 20

        // Logo
        Rectangle {
            width: 80; height: 80; radius: 20; color: "#F2F2F7"
            anchors.horizontalCenter: parent.horizontalCenter
            Image {
                anchors.fill: parent; anchors.margins: 15
                source: "file:assets/icons/logo.png"
                fillMode: Image.PreserveAspectFit
            }
        }

        // 标题
        Column {
            width: parent.width
            spacing: 5
            Label {
                text: "ViewStop"
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 20; font.bold: true; color: "#1d1d1f"
            }
            Label {
                text: "Version 1.0.8"
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 11; color: "#86868b"
            }
        }

        // 分割线
        Rectangle { 
            width: parent.width; height: 1; color: "#F2F2F7" 
        }

        // 4. 关键：换行文字
        Label {
            width: parent.width
            text: "我喜欢看电影，习惯是到网上到处找在线电影网站。有一天突然想到，这么到处找不如干脆写一个看电影的工具，于是事情就这么成了，虽然不够完美。各位有幸得到了我这个工具的朋友们，有空给我在GITHUB上反馈，以便使用起来体验更好.... 
            — 瓜哥"
            font.pixelSize: 14
            color: "#333333"
            wrapMode: Text.WordWrap // 自动换行
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 1.4
            font.italic: true
        }

        // 版权
        Label {
            width: parent.width
            text: "Created by GuaGe  •  2026"
            font.pixelSize: 11; color: "#aeaeb2"
            horizontalAlignment: Text.AlignHCenter
        }

        // 5. 按钮：直接作为 Column 的最后一个元素
        Button {
            text: "❤️❤️赞一个❤️❤️❤️"
            anchors.horizontalCenter: parent.horizontalCenter
            flat: true
            font.bold: true
            font.pixelSize: 14
            palette.buttonText: "#007AFF"
            onClicked: aboutDialog.close()
            
            // 增加一点底部边距
            bottomPadding: 20
        }
    }

    // 弹出动画
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200 }
            NumberAnimation { property: "scale"; from: 0.95; to: 1; duration: 250; easing.type: Easing.OutBack }
        }
    }
}