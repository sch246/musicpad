

import pygame
import keyboard

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QMessageBox
from PyQt6.QtCore import Qt
import yaml

from .global_settings import GlobalSettings
from .tracks import TracksContainer, AudioTrackWidget

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
        self.setup_connections()

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

    def setup_connections(self):
        self.global_settings_widget.stop_all_tracks_sign.connect(self.stop_all_tracks)


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
            <tr><td>左键拖拽/上下方向键</td><td>移动音轨</td></tr>
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


