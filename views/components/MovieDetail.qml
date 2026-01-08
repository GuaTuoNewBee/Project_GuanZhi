import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

Popup {
    id: detailPopup
    property var movieData: ({})
    
    onMovieDataChanged: {
    console.log("======= 深度探测开始 =======")
    console.log("尝试 type:", movieData.type)
    console.log("尝试 class_name:", movieData.class_name)
    console.log("尝试 category:", movieData.category)
    console.log("尝试 kind:", movieData.kind)
    console.log("======= 深度探测结束 =======")
}
    // 逻辑过滤：保留 m3u8，过滤解说和网页地址
    property var playGroups: {
        return (function() {
            let raw = movieData.play_groups || [];
            let filteredGroups = [];
            for (let i = 0; i < raw.length; i++) {
                let group = raw[i];
                if ((group.season_name || "").includes("解说")) continue;
                let episodes = (group.episodes || []).filter(ep => {
                    let url = (ep.url || "").toLowerCase();
                    return url.indexOf(".m3u8") !== -1 && url.indexOf(".html") === -1;
                });
                if (episodes.length > 0) {
                    filteredGroups.push({ "season_name": group.season_name, "episodes": episodes });
                }
            }
            return filteredGroups;
        })();
    }

    width: Math.max(parent.width * 0.9, 900)
    height: Math.max(parent.height * 0.85, 600)
    anchors.centerIn: parent
    modal: true
    focus: true

    background: Rectangle { radius: 20; color: "white" }

    contentItem: Item {
        ToolButton {
            text: "✕"; anchors.right: parent.right; anchors.top: parent.top; z: 10
            onClicked: detailPopup.close()
        }

        RowLayout {
            anchors.fill: parent; anchors.margins: 30; spacing: 30

            // --- 左侧：海报 ---
            Rectangle {
                Layout.preferredWidth: 260
                Layout.preferredHeight: 380
                Layout.alignment: Qt.AlignTop
                radius: 12; clip: true; color: "#F7FAFC"
                Image {
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectCrop
                    source: movieData.pic ? "image://poster/" + movieData.pic : ""
                }
            }

            // --- 右侧：内容区 ---
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; Layout.alignment: Qt.AlignTop; spacing: 12

                // 1. 视频名称
                Text {
                    text: movieData.name || ""
                    font.pixelSize: 28; font.bold: true; color: "#1A202C"
                    Layout.fillWidth: true
                }      
                

                // 2. 核心数据行：评分(浅蓝)  地区  类型  年份
                RowLayout {
                    spacing: 15
                    Layout.fillWidth: true
                    
                    Rectangle {
                        color: "#EBF8FF"; radius: 4
                        implicitWidth: scoreText.implicitWidth + 12; implicitHeight: 24
                        Text {
                            id: scoreText; anchors.centerIn: parent
                            text: "评分: " + (movieData.score || "0.0")
                            color: "#3182CE"; font.pixelSize: 13; font.bold: true
                        }
                    }

                    Text { text: "地区：" + (movieData.area || "-"); font.pixelSize: 13; color: "#4A5568" }
                    // ✅ 修正：确保显示 type_name
                    Text { text: "类型：" + (movieData.type_name || movieData.class_name || "-"); font.pixelSize: 13; color: "#4A5568" }
                    Text { text: "年份：" + (movieData.year || "-"); font.pixelSize: 13; color: "#4A5568" }
                }

                // 3. 导演与主演
                Column {
                    Layout.fillWidth: true; spacing: 4
                    Text { 
                        text: "<b>导演：</b>" + (movieData.director || "-")
                        font.pixelSize: 13; color: "#4A5568"; textFormat: Text.RichText
                    }
                    Text { 
                        width: parent.width
                        text: "<b>主演：</b>" + (movieData.actor || "-")
                        font.pixelSize: 13; color: "#4A5568"; textFormat: Text.RichText
                        wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight
                    }
                }

                // 4. 剧情简介 (✅ 取消水平滚动条)
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 5
                    Text { text: "<b>剧情简介：</b>"; font.pixelSize: 14; textFormat: Text.RichText; color: "#2D3748" }
                    ScrollView {
                        id: desScroll
                        Layout.fillWidth: true; Layout.preferredHeight: 80; clip: true
                        // ✅ 关键：禁用水平滚动条
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        background: Rectangle { color: "#F8FAFC"; radius: 6 }

                        Text { 
                            padding: 10
                            // ✅ 关键：强制宽度等于 ScrollView 宽度，实现自动换行
                            width: desScroll.availableWidth 
                            text: movieData.des || "暂无简介"
                            wrapMode: Text.WordWrap; color: "#718096"
                            font.pixelSize: 13; lineHeight: 1.4 
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#EDF2F7" }

                // 5. 选集播放
                Text { text: "选集播放"; font.pixelSize: 16; font.bold: true; color: "#2D3748" }
                ScrollView {
                    id: playScroll
                    Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    Column {
                        width: playScroll.availableWidth; spacing: 15
                        Repeater {
                            model: detailPopup.playGroups
                            delegate: ColumnLayout {
                                width: parent.width; spacing: 8
                                Text { text: "🎬 " + modelData.season_name; font.bold: true; color: "#3182CE"; font.pixelSize: 13 }
                                Flow {
                                    Layout.fillWidth: true; spacing: 10
                                    Repeater {
                                        model: modelData.episodes
                                        delegate: Button {
                                            id: epBtn
                                            text: modelData.name
                                            contentItem: Text {
                                                text: epBtn.text
                                                font.pixelSize: 12; color: epBtn.down ? "#2C5282" : "#3182CE"
                                                horizontalAlignment: Text.AlignHCenter
                                            }
                                            background: Rectangle {
                                                implicitWidth: 80; implicitHeight: 32
                                                color: epBtn.hovered ? "#EBF8FF" : "white"
                                                border.color: "#3182CE"; border.width: 1; radius: 4
                                            }
                                            onClicked: {
                                                if (typeof globalVideoPlayer !== "undefined") {
                                                    globalVideoPlayer.playVideo(modelData.url, movieData.name + " " + modelData.name)
                                                    detailPopup.close()
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}