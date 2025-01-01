import keyboard
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QRadioButton, QPushButton,QSlider,
                           QButtonGroup, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtMultimedia import QMediaDevices

OVERLAP = "重叠模式"
SINGLE = "单点模式"
PAUSE = "暂停模式"
STOP = "终止模式"


class ShortcutCatcher(QLabel):
    shortcutChanged = pyqtSignal(str)

    def __init__(self, text=""):
        super().__init__(text)
        self.capturing = False
        self.current_keys = []
        self.current_shortcut = ""
        self.hook = None
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if not self.capturing:
            self.start_capture()

    def start_capture(self):
        self.capturing = True
        self.setText("请按下快捷键...")
        self.current_keys.clear()
        self.hook = keyboard.hook(self._on_key_event)  # 存储钩子引用

    def stop_capture(self):
        self.capturing = False
        if self.hook:  # 只移除自己的钩子
            keyboard.unhook(self.hook)
            self.hook = None

    def _on_key_event(self, event):
        if not self.capturing:
            return

        if len(event.name) == 1:
            # 如果是组合键，将其转换为可读形式
            key = event.name.replace(" ", "_").upper()
        else:
            key = event.name.replace(" ", "_")

        if event.event_type == keyboard.KEY_DOWN:
            if key == "esc":
                self.current_keys.clear()
                self.setText("")
                self.current_shortcut = ""
                self.shortcutChanged.emit("")
                self.stop_capture()
                return

            if key in self.current_keys:
                return
            self.current_keys.append(key)
            key_text = "+".join(self.current_keys)
            self.setText(key_text)
            # 立即更新当前快捷键
            self.current_shortcut = key_text

        elif event.event_type == keyboard.KEY_UP:
            # 当任意键松开时，结束捕获并发送当前组合键
            if self.current_shortcut:  # 确保有快捷键被设置
                self.setText(self.current_shortcut)
                self.shortcutChanged.emit(self.current_shortcut)
            self.stop_capture()


class GlobalSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 创建一个框架来包含全局设置
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame_layout = QVBoxLayout(frame)

        # 触发模式设置
        first_row = QWidget()
        first_layout = QHBoxLayout(first_row)
        first_layout.setContentsMargins(0, 0, 0, 0)

        self.hold_radio = QRadioButton("按住触发")
        self.toggle_radio = QRadioButton("切换触发")
        self.toggle_radio.setChecked(True)
        self.stop_all_btn = QPushButton("停止所有")
        self.stop_all_shortcut = ShortcutCatcher()

        first_layout.addWidget(self.hold_radio)
        first_layout.addWidget(self.toggle_radio)
        first_layout.addWidget(self.stop_all_btn)
        first_layout.addWidget(self.stop_all_shortcut)
        first_layout.addStretch()# 添加到框架布局

        # 停止所有播放设置
        second_row = QWidget()
        second_layout = QHBoxLayout(second_row)
        second_layout.setContentsMargins(0, 0, 0, 0)

        self.device_combo = QComboBox()
        self.update_audio_devices()

        second_layout.addWidget(QLabel("音频设备:"))
        second_layout.addWidget(self.device_combo)
        second_layout.addStretch()



        frame_layout.addWidget(first_row)
        frame_layout.addWidget(second_row)

        # 添加到主布局
        layout.addWidget(frame)
        layout.addStretch()

    def setup_connections(self):
        # 连接停止所有按钮
        self.stop_all_btn.clicked.connect(self.on_stop_all_clicked)
        # 更改音频设备
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)

    def on_stop_all_clicked(self):
        if hasattr(self, 'parent') and isinstance(self.parent(), AudioPlayer):
            self.parent().stop_all_tracks()


    def update_audio_devices(self):
        self.device_combo.clear()
        for device in QMediaDevices.audioOutputs():
            self.device_combo.addItem(device.description())

    def on_device_changed(self, index):
        # 重新初始化pygame.mixer使用新的音频设备
        pygame.mixer.quit()
        try:
            # 获取选中的设备名称
            device_name = self.device_combo.currentText()
            pygame.mixer.init(devicename=device_name)
            pygame.mixer.set_num_channels(32)
        except Exception as e:
            print(f"切换音频设备失败: {e}")
            # 如果切换失败，尝试使用默认设备重新初始化
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32)

    def get_settings(self):
        return {
            "hold_mode": self.hold_radio.isChecked(),
            "stop_all_shortcut": self.stop_all_shortcut.current_shortcut
        }

    def load_settings(self, settings):
        if settings.get("hold_mode"):
            self.hold_radio.setChecked(True)
        else:
            self.toggle_radio.setChecked(True)

        shortcut = settings.get("stop_all_shortcut", "")
        self.stop_all_shortcut.setText(shortcut or "无快捷键")
        self.stop_all_shortcut.current_shortcut = shortcut






















# import wave

# def check_wav_info(file_path):
#     with wave.open(file_path, 'rb') as wav_file:
#         print(f"通道数: {wav_file.getnchannels()}")
#         print(f"采样宽度: {wav_file.getsampwidth()}")
#         print(f"采样率: {wav_file.getframerate()}")
#         print(f"帧数: {wav_file.getnframes()}")
#         print(f"参数: {wav_file.getparams()}")




import pygame
from pathlib import Path
from pygame.mixer import Channel

class AudioTrack:
    def __init__(self):
        self.sound = None
        self.channels: list[Channel] = []
        self.volume = 0
        self.is_playing = False
        self.is_paused = False
        self.loop = False
        self.mode = STOP
        self.path = ""

    def load_file(self, file_path:str):
        """加载音频文件"""
        if not file_path or not Path(file_path).exists():
            self.sound = None
            self.path = ""
            return False

        try:
            self.sound = pygame.mixer.Sound(file_path)
            self.path = file_path
            self.set_volume(self.volume*100)
            return True
        except Exception as e:
            print(f"加载音频文件失败: {e}")
            self.sound = None
            self.path = ""
            return False

    def toggle_play(self, is_hold_mode: bool, is_key_down: bool):
        """按状态播放音频"""
        if not self.sound:
            return

        # 切换触发： 按下 True 松开 按下 True 松开 按下 True ...
        # 按住触发: 按下 True 松开 False 按下 True ...
        # print('play', is_key_down)
        should_start = is_key_down if is_hold_mode else not self.is_active()
        self.cleanup_channels()

        if self.mode == OVERLAP:
            # 重叠模式：直接播放新实例
            if is_key_down:
                self.play()

        elif self.mode == SINGLE:
            # 单点模式：停止当前播放并重新开始
            if is_key_down:
                self.stop()
                self.play()

        elif self.mode == PAUSE:
            if should_start:
                if not self.is_playing:
                    # 新开始播放
                    self.play()
                elif self.is_paused:
                    # 继续播放
                    self.unpause()
            else:
                if self.is_playing:
                    # 暂停播放
                    self.pause()

        elif self.mode == STOP:
            # 终止模式：停止当前播放并重新开始
            self.stop()
            if should_start:
                self.play()

    def toggle_stop(self):
        '''播放/停止'''
        if not self.sound:
            return
        self.cleanup_channels()
        if self.is_active():
            self.stop()
        else:
            if self.is_paused:
                self.stop()
            self.play()

    def toggle_pause(self):
        '''播放/暂停/继续'''
        if not self.sound:
            return
        if not self.is_active():
            if not self.is_playing:
                # 新开始播放
                self.play()
            elif self.is_paused:
                # 继续播放
                self.unpause()
        else:
            if self.is_playing:
                # 暂停播放
                self.pause()

    def play(self):
        channel = self.sound.play(loops=-1 if self.loop else 0)
        self.channels.append(channel)
        self.is_playing = True
        self.is_paused = False

    def stop(self):
        """停止播放"""
        if self.sound:
            self.sound.stop()
        self.channels.clear()
        self.is_playing = False
        self.is_paused = False

    def pause(self):
        '''暂停播放'''
        for channel in self.channels:
            channel.pause()
        self.is_paused = True

    def unpause(self):
        '''继续播放'''
        for channel in self.channels:
            channel.unpause()
        self.is_paused = False
        self.is_playing = True

    def set_volume(self, db):
        """设置音量 (db)"""
        self.volume = max(-60, min(0, db))  # 限制在 -60dB 到 0dB 之间
        self.volume = pow(10, self.volume / 20.0)
        if self.sound:
            self.sound.set_volume(self.volume)

    def is_active(self):
        """检查是否正在播放"""
        return self.is_playing and not self.is_paused

    def cleanup_channels(self):
        """清理未在播放的通道"""
        self.channels = [ch for ch in self.channels
            if ch.get_busy() and ch.get_sound() is self.sound]

        if not self.channels:
            self.is_playing = False
            self.is_paused = False

















from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QApplication, QRadioButton, QPushButton, QFrame, QScrollArea, QLabel,
    QComboBox, QSlider, QSpinBox, QCheckBox, QFileDialog, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from pathlib import Path

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
        self.tracks_layout = QVBoxLayout(content_widget)
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

        # 连接添加音轨按钮
        self.add_track_btn.clicked.connect(self.add_track)
    def add_track(self):
        # 在按钮之前添加新音轨
        track_widget = AudioTrackWidget()
        track_widget.select_sign.connect(lambda checked: self.handle_track_selection(track_widget, checked))
        track_widget.focus_expand_sign.connect(lambda: self.handle_focus_expand(track_widget))
        self.tracks_layout.insertWidget(self.tracks_layout.count() - 1, track_widget)
        track_widget.tracks_layout = self.tracks_layout
        self.update_tab_order()  # 添加这行
        return track_widget

    def move_track(self, from_index, to_index):
        # 移动音轨位置
        track = self.tracks_layout.takeAt(from_index).widget()
        self.tracks_layout.insertWidget(to_index, track)
        track.setFocus()
        self.update_tab_order()  # 添加这行

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
































# main.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication, QScrollArea, QMenuBar, QMenu, QMessageBox
from PyQt6.QtCore import Qt
import sys
import yaml

class AudioPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化 pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(32)  # 设置最大同时播放通道数
        # 设置窗口基本属性
        self.setWindowTitle("音频播放器")
        self.setMinimumSize(400, 400)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(0)  # 减少间距
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 初始化UI
        self.init_ui()
        self.load_settings()

        # 快捷键
        self.active_shortcuts = {}  # 存储活跃的快捷键
        self.hold_keys = set()     # 存储当前按住的键
        self.setup_keyboard_hook()

    def init_ui(self):
        self.create_menu_bar()
        #添加全局设置
        self.global_settings_widget = GlobalSettings()
        self.global_settings_widget.setFixedHeight(90)  # 设置固定高度
        self.main_layout.addWidget(self.global_settings_widget)

        # 音轨容器占据剩余空间
        self.tracks_container = TracksContainer()
        self.tracks_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tracks_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.main_layout.addWidget(self.tracks_container)
        # 后续会在这里添加更多UI组件
        pass
    def load_settings(self):
        try:
            with open('audios.yaml', 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data:
                    self.global_settings_widget.load_settings(data.get('global_settings', {}))
                    for track_data in data.get('tracks', []):
                        track_widget = self.tracks_container.add_track()
                        track_widget.load_settings(track_data)
        except FileNotFoundError:
            pass
    def save_settings(self):
        tracks_data = []
        for i in range(self.tracks_container.tracks_layout.count() - 1):  # -1 排除添加按钮
            track = self.tracks_container.tracks_layout.itemAt(i).widget()
            tracks_data.append(track.get_settings())
        data = {
            'global_settings': self.global_settings_widget.get_settings(),
            'tracks': tracks_data
        }
        with open('audios.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)



    def setup_keyboard_hook(self):
        """设置全局键盘钩子"""
        keyboard.hook(self._on_key_event)

    def _on_key_event(self, event):
        """处理键盘事件"""
        # 将键名标准化
        if len(event.name) == 1:
            key = event.name.replace(" ", "_").upper()
        else:
            key = event.name.replace(" ", "_")

        if event.event_type == keyboard.KEY_DOWN:
            # 如果不是新按下的，skip
            if key in self.hold_keys:
                return
            self.hold_keys.add(key)
        elif event.event_type == keyboard.KEY_UP:
            self.hold_keys.discard(key)

        # 仅新按下的按钮
        # 和松开按钮


        # 检查是否是停止所有的快捷键
        stop_all_shortcut = self.global_settings_widget.stop_all_shortcut.current_shortcut
        stop_all_keys = stop_all_shortcut.split("+") if stop_all_shortcut else []
        # 如果新按下的键在范围内
        if stop_all_keys and event.event_type == keyboard.KEY_DOWN and key in stop_all_keys:
            # 检查是否所有需要的键都被按下
            if all(k in self.hold_keys for k in stop_all_keys):
                self.stop_all_tracks()

        # 获取当前的触发模式
        is_hold_mode = self.global_settings_widget.hold_radio.isChecked()
        # 处理音轨快捷键
        for i in range(self.tracks_container.tracks_layout.count() - 1):
            track_widget = self.tracks_container.tracks_layout.itemAt(i).widget()
            shortcut = track_widget.shortcut_catcher.current_shortcut

            # 如果新按下/松开的键在范围内
            if shortcut and key in shortcut.split("+"):
                # 按下时所有键满足
                if (event.event_type == keyboard.KEY_DOWN
                    and all(k in self.hold_keys for k in shortcut.split("+"))):
                    self.trigger_track(track_widget, True)
                # 松开按键仅在按住模式下有效
                # 此时松开任意范围的按钮都失效
                elif (event.event_type == keyboard.KEY_UP
                      and is_hold_mode):
                    self.trigger_track(track_widget, False)

    def trigger_track(self, track_widget: AudioTrackWidget, is_key_down):
        """触发音轨播放或停止"""
        # 仅在按下按钮，或者松开按钮且按住模式时有效
        # 也就是
        # 切换触发： 按下 True 松开 按下 True 松开 按下 True ...
        # 按住触发: 按下 True 松开 False 按下 True ...

        # 如果设置了停止其他，先停止其他音轨
        # 在音乐播放的开始和结束都会尝试停止
        is_active = track_widget.audio_track.is_active()
        if not is_active and track_widget.mute_others_check.isChecked():
            self.stop_other_tracks(track_widget)

        is_hold_mode = self.global_settings_widget.hold_radio.isChecked()
        track_widget.audio_track.toggle_play(is_hold_mode, is_key_down)

    def stop_all_tracks(self):
        """停止所有音轨播放"""
        for i in range(self.tracks_container.tracks_layout.count() - 1):
            track_widget = self.tracks_container.tracks_layout.itemAt(i).widget()
            track_widget.audio_track.stop()

    def stop_other_tracks(self, current_track):
        """停止除了指定音轨外的所有其他音轨"""
        for i in range(self.tracks_container.tracks_layout.count() - 1):
            track_widget = self.tracks_container.tracks_layout.itemAt(i).widget()
            if track_widget != current_track:
                track_widget.audio_track.stop()


    def closeEvent(self, event):
        keyboard.unhook_all()  # 移除键盘钩子
        pygame.mixer.quit()    # 关闭音频系统
        # 窗口关闭时保存设置
        self.save_settings()
        super().closeEvent(event)

    def create_menu_bar(self):
        # 创建菜单栏
        menubar = self.menuBar()# 创建帮助菜单
        help_menu = menubar.addMenu('帮助')

        # 创建关于动作
        about_action = help_menu.addAction('关于')
        about_action.triggered.connect(self.show_about_dialog)

        # 创建使用说明动作
        manual_action = help_menu.addAction('使用说明')
        manual_action.triggered.connect(self.show_manual_dialog)

    def show_about_dialog(self):
        about_text = """
        <h3>音频播放器</h3>
        <p>版本: 1.0</p>
        <p>作者: sch246</p>
        <p>联系方式: sch246@qq.com</p>
        <p>Copyright © 2024 All Rights Reserved</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def show_manual_dialog(self):
        manual_text = """
        <h3>使用说明</h3>
        <p><b>播放模式：</b></p>
        <ul>
            <li>重叠模式：每次点击从头播放，不终止之前的播放</li>
            <li>单点模式：每次点击从头播放</li>
            <li>暂停模式：停止播放时暂停内容</li>
            <li>终止模式：停止播放时终止内容（默认选择）</li>
        </ul>
        <p><b>快捷操作：</b></p>
        <table>
            <tr><td>可以拖入音频文件-----------------</td></tr>
            <tr><td>tab 和 shift+tab</td><td>切换选择</td></tr>
            <tr><td>上下方向键</td><td>移动音轨</td></tr>
            <tr><td>Delete</td><td>删除音轨</td></tr>
            <tr><td>Enter</td><td>播放/停止</td></tr>
            <tr><td>左键方块</td><td>播放/暂停/继续</td></tr>
            <tr><td>右键方块</td><td>停止</td></tr>
            <tr><td>双击名称</td><td>选择音频</td></tr>
            <tr><td>右键/Space</td><td>展开/折叠</td></tr>
            <tr><td>双击右键</td><td>展开目标并折叠其它</td></tr>
        </table>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("使用说明")
        msg.setText(manual_text)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.exec()


def main():
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
