import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import Qt5Compat.GraphicalEffects

Rectangle {
    id: playerLayer
    anchors.fill: parent
    color: "#000000"
    visible: false
    z: 9999

    property alias source: mediaPlayer.source
    property string title: ""
    property bool controlsVisible: true
    property bool isFullScreen: false

    function playVideo(url, movieTitle) {
        console.log("🎬 尝试播放 URL:", url)
        mediaPlayer.retryCount = 0
        mediaPlayer.stop()
        
        // 注意：某些环境下直接加 ffmpegHeaders 到 source 字符串可能需要后端支持
        // 这里保持 source 赋值逻辑简洁
        source = url 
        title = movieTitle
        visible = true
        
        playDelayTimer.restart()
        uiTimer.restart()
    }

    function toggleFullScreen() {
        if (!isFullScreen) {
            window.showFullScreen()
            isFullScreen = true
        } else {
            window.showNormal()
            isFullScreen = false
        }
    }

    MediaPlayer {
        id: mediaPlayer
        videoOutput: videoOutput
        audioOutput: AudioOutput { id: audioOutput }
        
        property int retryCount: 0

        onErrorOccurred: (error, errorString) => {
            console.log("❌ 播放错误: " + errorString)
            if (retryCount < 3 && source !== "") {
                retryCount++
                retryTimer.restart()
            }
        }
    }

    Timer {
        id: retryTimer
        interval: 1500
        onTriggered: {
            let lastUrl = mediaPlayer.source
            mediaPlayer.source = ""
            mediaPlayer.source = lastUrl
            mediaPlayer.play()
        }
    }

    Timer { id: playDelayTimer; interval: 200; onTriggered: mediaPlayer.play() }

    VideoOutput {
        id: videoOutput
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectFit
        
        BusyIndicator {
            id: loadingBus
            anchors.centerIn: parent
            implicitWidth: 48; implicitHeight: 48
            running: (mediaPlayer.playbackState === MediaPlayer.PlayingState && mediaPlayer.bufferProgress < 1.0) 
                     || mediaPlayer.playbackState === MediaPlayer.LoadingState
            visible: running
            
            contentItem: Item {
                Rectangle {
                    width: parent.width; height: parent.height
                    color: "transparent"; radius: width/2
                    border.width: 3; border.color: "#3182CE"
                    RotationAnimator on rotation {
                        from: 0; to: 360; duration: 800; loops: Animation.Infinite; running: loadingBus.running
                    }
                }
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onPositionChanged: { playerLayer.controlsVisible = true; uiTimer.restart() }
        onClicked: {
            playerLayer.controlsVisible = true
            uiTimer.restart()
            if (mediaPlayer.playbackState === MediaPlayer.PlayingState) mediaPlayer.pause()
            else mediaPlayer.play()
        }
        onDoubleClicked: toggleFullScreen()
    }

    // --- 顶部状态栏 ---
    Rectangle {
        id: topBar
        anchors.top: parent.top
        width: parent.width; height: 50
        opacity: playerLayer.controlsVisible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 300 } }
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#AA000000" }
            GradientStop { position: 1.0; color: "transparent" }
        }

        RowLayout {
            anchors.fill: parent; anchors.margins: 15
            ToolButton {
                padding: 5
                background: null // 💡 移除灰色背景
                contentItem: Text { 
                    text: "←" 
                    color: "white"
                    font.pixelSize: 22; horizontalAlignment: Text.AlignHCenter 
                }
                onClicked: { mediaPlayer.stop(); playerLayer.visible = false; mediaPlayer.source = "" }
            }
            Text {
                text: playerLayer.title
                color: "white"; font.pixelSize: 15; font.weight: Font.Medium; Layout.fillWidth: true; elide: Text.ElideRight
            }
        }
    }

    // --- 底部控制面板 ---
    Rectangle {
        id: controlPanel
        anchors.bottom: parent.bottom; anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 15
        width: parent.width * 0.92; height: 54; radius: 27 
        color: "#EE1A202C" 
        opacity: playerLayer.controlsVisible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 300 } }
        
        layer.enabled: true
        layer.effect: DropShadow { radius: 10; color: "#88000000"; samples: 15 }

        RowLayout {
            anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20
            spacing: 12

            ToolButton {
                id: playBtn
                Layout.preferredWidth: 30
                background: null // 💡 移除灰色背景
                contentItem: Text {
                    text: mediaPlayer.playbackState === MediaPlayer.PlayingState ? "⏸" : "▶"
                    color: "white"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter
                }
                onClicked: {
                    mediaPlayer.playbackState === MediaPlayer.PlayingState ? mediaPlayer.pause() : mediaPlayer.play()
                    uiTimer.restart()
                }
            }

            Text { text: formatTime(mediaPlayer.position); color: "#CBD5E0"; font.pixelSize: 11; font.family: "Monospace" }

            Slider {
                id: seekSlider
                Layout.fillWidth: true
                from: 0; to: mediaPlayer.duration; value: mediaPlayer.position
                
                background: Rectangle {
                    height: 4; radius: 2; color: "#44FFFFFF"
                    Rectangle { 
                        width: seekSlider.visualPosition * parent.width
                        height: 4; color: "#3182CE"; radius: 2 
                    }
                    Rectangle {
                        width: mediaPlayer.bufferProgress * parent.width
                        height: 4; color: "#22FFFFFF"; radius: 2
                    }
                }
                handle: Rectangle {
                    x: seekSlider.visualPosition * (seekSlider.availableWidth - 12); y: parent.height/2-6
                    width: 12; height: 12; radius: 6; color: "white"
                }
                onMoved: { mediaPlayer.position = value; uiTimer.restart() }
            }

            Text { text: formatTime(mediaPlayer.duration); color: "#CBD5E0"; font.pixelSize: 11; font.family: "Monospace" }
            
            ToolButton {
                Layout.preferredWidth: 30
                background: null // 💡 移除灰色背景
                contentItem: Text { text: "🔊"; color: "white"; font.pixelSize: 16; horizontalAlignment: Text.AlignHCenter }
                onClicked: volumePopup.open()
                Popup {
                    id: volumePopup; y: -115; x: -8; width: 34; height: 100
                    background: Rectangle { color: "#F7FAFC"; radius: 17 } 
                    Slider {
                        anchors.centerIn: parent; orientation: Qt.Vertical; height: 80
                        from: 0; to: 1.0; value: audioOutput.volume
                        onMoved: audioOutput.volume = value
                        // 💡 为音量条增加简单的槽位背景
                        background: Rectangle {
                            implicitWidth: 4; implicitHeight: 80
                            x: parent.leftPadding + parent.availableWidth / 2 - width / 2
                            y: parent.topPadding
                            width: 4; height: parent.availableHeight; radius: 2; color: "#E2E8F0"
                        }
                    }
                }
            }

            ToolButton {
                Layout.preferredWidth: 30
                background: null // 💡 移除灰色背景
                contentItem: Text { 
                    text: playerLayer.isFullScreen ? "❐" : "▢"
                    color: "white"; font.pixelSize: 18; horizontalAlignment: Text.AlignHCenter 
                }
                onClicked: toggleFullScreen()
            }
        }
    }

    Timer { id: uiTimer; interval: 3500; onTriggered: playerLayer.controlsVisible = false }

    function formatTime(ms) {
        if (ms <= 0) return "00:00"
        var totalSeconds = Math.floor(ms / 1000);
        var minutes = Math.floor(totalSeconds / 60);
        var seconds = totalSeconds % 60;
        return (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
    }
}