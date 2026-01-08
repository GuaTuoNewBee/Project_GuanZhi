import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    // 💡 自动高度计算：列内容高度 + 上下边距
    implicitHeight: filterCol.implicitHeight + 40
    Layout.fillWidth: true

    property string currentMainType: "电影"
    signal filterChanged(string key, string value)

    // ✅ 数据字典：已扩展发达国家及 2010 年份
    readonly property var filterMap: {
        "电影": [
            { key: "type_name", label: "类型", tags: ["全部", "动作片", "喜剧片", "爱情片", "科幻片", "恐怖片", "惊悚片", "剧情片", "战争片", "剧情片", "其他"] },
            { key: "area", label: "地区", tags: ["全部", "中国大陆", "中国香港", "中国台湾", "美国", "英国", "法国", "德国", "日本", "韩国", "加拿大", "澳大利亚", "意大利", "西班牙", "俄罗斯", "其他"] },
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010", "更早"] }
        ],
        "电视剧": [
            { key: "area", label: "地区", tags: ["全部", "中国大陆", "中国香港", "中国台湾", "美国", "英国", "韩国", "日本", "泰国", "新加坡", "其他"] },
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010", "更早"] }
        ],
        "动漫": [
            { key: "area", label: "地区", tags: ["全部", "日本", "中国大陆", "美国", "韩国", "其他"] },
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "2015-2019", "2010-2014", "更早"] }
        ],
        "综艺": [
            { key: "area", label: "地区", tags: ["全部", "中国大陆", "韩国", "中国台湾", "中国香港", "日本", "美国", "其他"] },
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "更早"] }
        ],
        "纪录片": [
            { key: "area", label: "地区", tags: ["全部", "美国", "英国", "中国大陆", "法国", "德国", "日本", "其他"] },
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "更早"] }
        ],
        "短剧": [
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "更早"] }
        ],
        "体育": [
            { key: "season", label: "赛季", tags: ["全部", "2025-26", "2024-25", "2023-24", "2022-23", "更早"] },
            { key: "type", label: "类型", tags: ["全部", "足球", "篮球", "网球", "赛车", "其他"] }
        ],
        "伦理电影": [ 
            { 
                key: "area", 
                label: "地区", 
                // 💡 这里的文字改为和数据库探测到的一致
                tags: ["全部", "日本", "韩国", "香港", "台湾", "美国", "法国", "其它"] 
            },
            { 
                key: "year", 
                label: "年份", 
                tags: ["全部", "2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "更早"] 
            }
        ],
        "电影解说": [
            { key: "area", label: "地区", tags: ["全部", "中国大陆", "韩国", "美国", "日本", "其他"] },
            { key: "year", label: "年份", tags: ["全部", "2026", "2025", "2024", "2023", "2022", "更早"] }
        ]
    }

    ColumnLayout {
        id: filterCol
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // --- 1. 动态过滤行 ---
        Repeater {
            model: root.filterMap[root.currentMainType] || []
            delegate: RowLayout {
                id: filterRow
                spacing: 15
                Layout.fillWidth: true
                readonly property string rowKey: modelData.key
                property string selectedValue: "全部"

                Text {
                    text: modelData.label
                    color: "#718096"
                    font.pixelSize: 13
                    font.weight: Font.Medium
                    Layout.preferredWidth: 40
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: modelData.tags
                        delegate: Button {
                            id: tagBtn
                            text: modelData
                            property bool isSelected: text === filterRow.selectedValue

                            contentItem: Text {
                                text: tagBtn.text
                                color: tagBtn.isSelected ? "#2196F3" : (tagBtn.hovered ? "#2D3748" : "#4A5568")
                                font.pixelSize: 12
                                font.bold: tagBtn.isSelected
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                            }

                            background: Rectangle {
                                implicitWidth: Math.max(54, contentItem.implicitWidth + 24)
                                implicitHeight: 28
                                color: tagBtn.isSelected ? "#EBF8FF" : (tagBtn.hovered ? "#EDF2F7" : "transparent")
                                radius: 14
                            }

                            onClicked: {
                                filterRow.selectedValue = text;
                                root.filterChanged(filterRow.rowKey, text);
                            }
                        }
                    }
                }
            }
        }

        // --- 分割线 ---
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: "#EDF2F7"
            Layout.topMargin: 5
            Layout.bottomMargin: 5
        }

        // --- 2. 排序行 ---
        RowLayout {
            id: orderRow
            spacing: 15
            Layout.fillWidth: true
            property string selectedOrder: "time"

            Text {
                text: "排序"
                color: "#718096"
                font.pixelSize: 13
                font.weight: Font.Medium
                Layout.preferredWidth: 40
            }

            Flow {
                Layout.fillWidth: true
                spacing: 20
                Repeater {
                    model: [
                        { text: "最近更新", val: "time" },
                        { text: "人气最高", val: "hits" },
                        { text: "评分最高", val: "score" },                        
                    ]
                    delegate: Text {
                        id: orderText
                        text: modelData.text
                        font.pixelSize: 13
                        property bool isSelected: modelData.val === orderRow.selectedOrder
                        color: isSelected ? "#2196F3" : (orderMouse.containsMouse ? "#2D3748" : "#4A5568")
                        font.bold: isSelected

                        MouseArea {
                            id: orderMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                orderRow.selectedOrder = modelData.val;
                                root.filterChanged("order", modelData.val);
                            }
                        }
                    }
                }
            }
        }
    }
}