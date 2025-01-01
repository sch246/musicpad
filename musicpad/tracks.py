
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QScrollArea, QLabel,
    QComboBox, QSlider, QSpinBox, QCheckBox, QFileDialog, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from pathlib import Path

from .shortcut import ShortcutCatcher
from .audio_track import AudioTrack, OVERLAP, SINGLE, PAUSE, STOP

class AudioTrackWidget(QFrame):
    select_sign = pyqtSignal(bool)  # 选中信号
    focus_expand_sign = pyqtSignal()  # '折叠其它'信号
    tracks_layout: QVBoxLayout

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_track = AudioTrack()
        self.is_selected = False
        self.path = ""
        self.is_expanded = False
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.init_ui()
        self.setAcceptDrops(True)


        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_channels_status)
        self.check_timer.start(100)  # 每100ms检查一次

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                self.set_file(file_path)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # 第一行（始终显示）
        first_row_widget = QWidget()
        first_row = QHBoxLayout(first_row_widget)
        first_row.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        first_row.setSpacing(10)

        # 添加状态指示器到第一行
        self.status_indicator = QFrame()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setFrameStyle(QFrame.Shape.Box)
        self.update_status_indicator(False, False)

        # 名字标签，设置为自动扩展
        self.name_label = QLabel("未选择文件")
        self.name_label.setMinimumWidth(100)
        self.name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,# 水平方向扩展
            QSizePolicy.Policy.Preferred   # 垂直方向固定
        )
        self.name_label.setToolTip("双击选择文件")

        # 快捷键和展开按钮固定宽度，右对齐
        self.shortcut_catcher = ShortcutCatcher()
        self.shortcut_catcher.setFixedWidth(150)
        # self.expand_btn = QPushButton("...")
        # self.expand_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.expand_btn.setFixedWidth(30)

        # 删除按钮
        self.delete_btn = QPushButton("X")
        self.delete_btn.setFixedSize(23, 23)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #00000000;
                border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                color: white;
            }
        """)

        first_row.addWidget(self.status_indicator)
        first_row.addWidget(self.name_label)
        first_row.addWidget(self.shortcut_catcher)
        # first_row.addWidget(self.expand_btn)
        first_row.addWidget(self.delete_btn)

        # 第二行（展开时显示）
        volume_row = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(-60, 0)
        self.volume_slider.setValue(0)
        self.volume_input = QSpinBox()
        self.volume_input.setRange(-60, 0)
        self.volume_input.setValue(0)
        self.volume_input.setFixedWidth(60)
        self.volume_input.setSuffix(" dB")
        volume_row.addWidget(QLabel("音量:"))
        volume_row.addWidget(self.volume_slider)
        volume_row.addWidget(self.volume_input)
        # 第三行（展开时显示）
        control_row = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([OVERLAP, SINGLE, PAUSE, STOP])
        self.mode_combo.setCurrentText(STOP)
        self.loop_check = QCheckBox("循环播放")
        self.mute_others_check = QCheckBox("停止其它")
        control_row.addWidget(self.mode_combo)
        control_row.addWidget(self.loop_check)
        control_row.addWidget(self.mute_others_check)
        control_row.addStretch()

        # 创建容器来存放可展开的行
        self.expandable_widget = QWidget()
        expandable_layout = QVBoxLayout(self.expandable_widget)
        expandable_layout.addLayout(volume_row)
        expandable_layout.addLayout(control_row)
        self.expandable_widget.hide()

        # 添加所有行到主布局
        self.main_layout.addWidget(first_row_widget)
        self.main_layout.addWidget(self.expandable_widget)# 设置固定高度

        self.setup_connections()

    def setup_connections(self):
        self.status_indicator.mousePressEvent = self.toggle_status
        # self.expand_btn.clicked.connect(self.toggle_expand)
        self.delete_btn.clicked.connect(self.deleteLater)
        self.volume_slider.valueChanged.connect(self.volume_input.setValue)
        self.volume_input.valueChanged.connect(self.volume_slider.setValue)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.loop_check.stateChanged.connect(self.on_loop_changed)
        self.name_label.mouseDoubleClickEvent = self.on_name_double_click

    def check_channels_status(self):
        """定期检查通道状态"""
        self.audio_track.cleanup_channels()
        self.update_status_indicator(self.audio_track.is_playing,
                                     self.audio_track.is_paused)

    def update_status_indicator(self, is_playing, is_paused):
        """更新状态指示器颜色"""
        self.status_indicator.setStyleSheet(
            "background-color: #aaaaaa;" if not is_playing else "background-color: #e6e219;" if is_paused else
            "background-color: #2ecc71;"
        )

    def toggle_status(self, event: QMouseEvent = None):
        '''切换播放状态'''
        is_active = self.audio_track.is_active()
        if not is_active and self.mute_others_check.isChecked():
            for i in range(self.tracks_layout.count() - 1):
                widget = self.tracks_layout.itemAt(i).widget()
                if widget != self:
                    widget.audio_track.stop()
        if event is None:
            self.audio_track.toggle_stop()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.audio_track.toggle_pause()
        elif event.button() == Qt.MouseButton.RightButton:
            self.audio_track.stop()

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.expandable_widget.setVisible(self.is_expanded)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.select_sign.emit(True)

    def mousePressEvent(self, event):
        '''右键点击展开'''
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.RightButton:
            self.toggle_expand()

    def set_selected(self, selected):
        self.is_selected = selected
        # 设置选中状态的样式
        self.setStyleSheet("""
            AudioTrackWidget[selected="true"] {
                border: 2px solid #0078D7;
                background-color: #E5F3FF;
            }
        """)
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def focusOutEvent(self, event):
        self.select_sign.emit(False)


    def set_file(self, file_path):
        self.path = file_path

        if self.audio_track.load_file(file_path):
            name = Path(file_path).name
            if len(name) > 40:
                name = name[:37] + "..."
            self.name_label.setText(name)
            self.name_label.setToolTip(str(file_path))
        else:
            self.name_label.setText("加载失败")
            self.name_label.setToolTip("文件加载失败")

    def on_volume_changed(self, value):
        self.audio_track.set_volume(value)

    def on_mode_changed(self, mode_text):
        self.audio_track.mode = mode_text

    def on_loop_changed(self, state):
        self.audio_track.loop = state == Qt.CheckState.Checked

    def on_name_double_click(self, event):
        '''双击选择文件，双击右键时聚焦展开'''
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择音频文件",
                "",
                "音频文件 (*.mp3 *.wav *.ogg *.flac);;所有文件 (*.*)"
            )
            if file_path:
                self.set_file(file_path)
        elif event.button() == Qt.MouseButton.RightButton:
            self.focus_expand_sign.emit()

    def get_settings(self):
        return {
            "file_path": self.path,
            "volume": self.volume_slider.value(),
            "shortcut": self.shortcut_catcher.current_shortcut,
            "mode": self.mode_combo.currentText(),
            "loop": self.loop_check.isChecked(),
            "mute_others": self.mute_others_check.isChecked()
        }

    def load_settings(self, settings):
        if settings.get("file_path"):
            self.set_file(settings["file_path"])
        self.volume_slider.setValue(settings.get("volume", 100))
        self.shortcut_catcher.setText(settings.get("shortcut", ""))
        self.shortcut_catcher.current_shortcut = settings.get("shortcut", "")
        self.mode_combo.setCurrentText(settings.get("mode", STOP))
        self.loop_check.setChecked(settings.get("loop", False))
        self.audio_track.loop = settings.get("loop", False)
        self.mute_others_check.setChecked(settings.get("mute_others", False))

from musicpad.draggable import DraggableVBoxLayout

class TracksContainer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_track: AudioTrackWidget = None
        self.init_ui()
        self.update_tab_order()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                track_widget = self.add_track()
                track_widget.load_settings({
                    'file_path': file_path
                })

    def init_ui(self):
        # 创建内容窗口
        content_widget = QWidget()
        self.tracks_layout = DraggableVBoxLayout(content_widget)
        self.tracks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.tracks_layout.addStretch()

        # 设置滚动区域属性
        self.setWidget(content_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 添加音轨按钮
        self.add_track_btn = QPushButton("添加音轨")
        self.tracks_layout.addWidget(self.add_track_btn)
        self.tracks_layout.setFixed(self.add_track_btn)

        # 连接添加音轨按钮
        self.add_track_btn.clicked.connect(self.add_track)
    def add_track(self):
        # 在按钮之前添加新音轨
        track_widget = AudioTrackWidget()
        track_widget.select_sign.connect(lambda checked: self.handle_track_selection(track_widget, checked))
        track_widget.focus_expand_sign.connect(lambda: self.handle_focus_expand(track_widget))
        self.tracks_layout.insertWidget(self.tracks_layout.count() - 1, track_widget)
        self.tracks_layout.setDraggable(track_widget)
        track_widget.tracks_layout = self.tracks_layout
        self.update_tab_order()
        return track_widget

    def move_track(self, from_index, to_index):
        # 移动音轨位置
        track = self.tracks_layout.takeAt(from_index).widget()
        self.tracks_layout.insertWidget(to_index, track)
        track.setFocus()
        self.update_tab_order()

    def update_tab_order(self):
        """更新Tab键顺序"""
        track_count = self.tracks_layout.count() - 1  # -1 排除添加按钮
        if track_count <= 1:
            return

        # 设置相邻音轨之间的Tab顺序
        for i in range(track_count - 1):
            current_track = self.tracks_layout.itemAt(i).widget()
            next_track = self.tracks_layout.itemAt(i + 1).widget()
            QWidget.setTabOrder(current_track, next_track)

        # 最后一个音轨连接到添加按钮
        last_track = self.tracks_layout.itemAt(track_count - 1).widget()
        QWidget.setTabOrder(last_track, self.add_track_btn)

    def handle_track_selection(self, selected_track, checked):
        for i in range(self.tracks_layout.count() - 1):# -1 排除添加按钮
            track = self.tracks_layout.itemAt(i).widget()
            if track == selected_track:
                track.set_selected(checked)
            else:
                track.set_selected(False)
        if checked:
            self.selected_track = selected_track
        else:
            self.selected_track = None

    def handle_focus_expand(self, widget):
        for i in range(self.tracks_layout.count() - 1):
            track = self.tracks_layout.itemAt(i).widget()
            if track != widget and track.is_expanded:
                track.toggle_expand()
            elif track is widget and not track.is_expanded:
                track.toggle_expand()

    def keyPressEvent(self, event):
        if not self.selected_track:
            return

        current_index = self.tracks_layout.indexOf(self.selected_track)

        if event.key() == Qt.Key.Key_Delete:
            # 删除当前选中的音轨
            self.tracks_layout.removeWidget(self.selected_track)
            self.selected_track.deleteLater()
            self.selected_track = None

            next_index = current_index - 1
            track_count = self.tracks_layout.count() - 1  # -1 for add button
            if track_count > 0:
                if next_index < 0:
                    next_index = 0  # Select first track if no track above

                next_track = self.tracks_layout.itemAt(next_index).widget()
                next_track.setFocus()

        elif event.key() == Qt.Key.Key_Space:
            # 展开或折叠选中的音轨
            self.selected_track.toggle_expand()

        elif event.key() == Qt.Key.Key_Up and current_index > 0:
            # 向上移动选中的音轨
            self.move_track(current_index, current_index - 1)

        elif event.key() == Qt.Key.Key_Down and current_index < self.tracks_layout.count() - 2:
            # 向下移动选中的音轨
            self.move_track(current_index, current_index + 1)

        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.selected_track.toggle_status()

