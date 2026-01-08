import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import "./components"

Item {
    id: moviesPage

    property int sidePadding: 40
    property string currentMainCategory: "电影"
    
    // 💡 1. 添加刷新因子变量
    property int imgUpdateTicket: 0

    function updateSubFilter(mainCat) {
        moviesPage.currentMainCategory = mainCat;
        if (filterArea) {
            filterArea.currentMainType = mainCat;
        }    
        GZBridge.set_main_type(mainCat);
    }

    Connections {
        target: GZBridge
        
        // 💡 2. 监听后台下载完成信号，自增 Ticket 强制 UI 重新刷图
        function onResultsChanged() {
            moviesPage.imgUpdateTicket++;
        }

        function onMovieDetailChanged() {
            let fullDetail = GZBridge.movieDetail;
            if (fullDetail && fullDetail.play_groups) {
                detailPopup.movieData = fullDetail;
            }
            if (!detailPopup.opened) detailPopup.open();
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#F8F9FA"
        z: -1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: moviesPage.sidePadding
        anchors.rightMargin: moviesPage.sidePadding
        anchors.topMargin: 20
        anchors.bottomMargin: 0
        spacing: 20

        BrandSearchInput {
            Layout.fillWidth: true
            Layout.preferredHeight: 75
            onSearchTriggered: txt => GZBridge.search(txt)
            onRefreshClicked: () => GZBridge.load_page(1) 
        }

        Rectangle {
            id: filterContainer
            Layout.fillWidth: true
            Layout.preferredHeight: filterArea.implicitHeight
            color: "white"
            radius: 12
            clip: true
            border.color: "#E2E8F0"
            border.width: 1

            QueryArea {
                id: filterArea
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                currentMainType: moviesPage.currentMainCategory
                onFilterChanged: (key, value) => {
                    GZBridge.set_filter(key, value);
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            GridView {
                id: movieGrid
                anchors.fill: parent
                clip: true
                cellWidth: width / Math.max(1, Math.floor(width / 180))
                cellHeight: cellWidth * 1.55
                model: GZBridge.results
                
                cacheBuffer: 1500
                keyNavigationEnabled:false
                interactive:true
                onModelChanged: {
                    contentY = 0
                }

                delegate: Item {
                    width: movieGrid.cellWidth
                    height: movieGrid.cellHeight
                    
                    Rectangle {
                        id: cardContainer
                        width: parent.width - 20
                        height: parent.height - 20
                        anchors.centerIn: parent
                        radius: 12
                        color: "white"                        
                        border.color: mouseArea.containsMouse ? "#2196F3" : "#E2E8F0"
                        border.width: mouseArea.containsMouse ? 2 : 1
                        scale: mouseArea.containsMouse ? 1.02 : 1.0

                        Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }
                        Behavior on border.color { ColorAnimation { duration: 150 } }

                        Rectangle {
                            id: posterRect
                            width: parent.width
                            height: parent.height * 0.78
                            radius: 10
                            clip: true
                            anchors.top: parent.top
                            color: "#EDF2F7"

                            Image {
                                anchors.fill: parent
                                // 💡 3. 修改 source，挂载刷新 Ticket。
                                // 只要 imgUpdateTicket 变了，QML 就会重新向 ImageProvider 发起请求。
                                source: modelData.pic ? ("image://poster/" + modelData.pic + "?v=" + moviesPage.imgUpdateTicket) : ""
                                
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                cache: true
                                sourceSize.width: parent.width
                                sourceSize.height: parent.height
                                opacity: status === Image.Ready ? 1 : 0
                                Behavior on opacity { NumberAnimation { duration: 300 } }
                            }
                        }

                        Column {
                            anchors.top: posterRect.bottom
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.margins: 12
                            spacing: 4
                            
                            Text {
                                width: parent.width
                                text: modelData.clean_name || modelData.name || "未知名称"
                                font.pixelSize: 14
                                font.bold: mouseArea.containsMouse
                                color: mouseArea.containsMouse ? "#2196F3" : "#2D3748"
                                elide: Text.ElideRight
                            }
                            Text {
                                text: modelData.remarks || "HD"
                                font.pixelSize: 11
                                color: "#718096"
                                elide: Text.ElideRight
                                width: parent.width
                            }
                        }

                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            
                            onClicked: {
                                detailPopup.movieData = modelData; 
                                detailPopup.open();
                                GZBridge.get_detail(modelData.id, modelData);
                            }
                        }
                    }
                }
            }
        }
    }

    MovieDetail {
        id: detailPopup
    }
}