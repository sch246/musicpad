import keyboard
from PyQt6.QtWidgets import (QLabel,QFrame)
from PyQt6.QtCore import Qt, pyqtSignal


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