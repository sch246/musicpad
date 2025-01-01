import keyboard, pygame
from PyQt6.QtWidgets import (QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QRadioButton, QPushButton,QSlider,
                           QButtonGroup, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtMultimedia import QMediaDevices

from musicpad.shortcut import ShortcutCatcher

OVERLAP = "重叠模式"
SINGLE = "单点模式"
PAUSE = "暂停模式"
STOP = "终止模式"


class GlobalSettings(QWidget):
    stop_all_tracks_sign = pyqtSignal()  # '停止所有'信号
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
        first_layout.addStretch()

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
        self.stop_all_btn.clicked.connect(self.stop_all_tracks_sign.emit)
        # 更改音频设备
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)


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