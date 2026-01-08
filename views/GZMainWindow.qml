import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import "./components" 

ApplicationWindow {
    id: window
    width: 1200 
    height: 800
    visible: true
    color: "#F8F9FA"
    title: "观止 - 电影聚合播放器"

    readonly property int globalSideMargin: 40 

    // 1. 主布局
    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        NavBar {
            id: topNavBar
            Layout.fillWidth: true
            // 💡 删掉了这里的 onCompleted，统一在最下面处理
            onCategoryChanged: cat => {
                GZBridge.set_filter("category_name", cat);
                moviesView.updateSubFilter(cat);
            }
        }

        MoviesWindow {
            id: moviesView
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        Rectangle {
            id: footer
            Layout.fillWidth: true
            Layout.preferredHeight: 70 
            color: "white"

            Rectangle {
                width: parent.width; height: 1; color: "#E2E8F0"
                anchors.top: parent.top
            }

            Pager {
                id: pagerInstance
                anchors.centerIn: parent 
                width: parent.width * 0.8 
            }
        }
    }

    // 2. 全局播放器层
    VideoPlayer {
        id: globalVideoPlayer
        anchors.fill: parent
        z: 9999
    }

    // ✨ 终极合并：全站【唯一】的初始化入口，彻底解决报错
    Component.onCompleted: {
        console.log("🚀 观止系统 UI 渲染完成，窗口已弹出");
        
        // 1. 设置导航栏视觉状态
        topNavBar.activeCategory = "电影";
        
        // 2. 异步请求第一页数据 (窗口现在是可见的，用户不会看到白屏)
        console.log("🚀 正在异步抓取首屏内容...");
        GZBridge.init_first_page(); 
    }
}