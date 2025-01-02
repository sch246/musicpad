import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from musicpad import AudioPlayer

def resource_path(relative_path):
    """获取资源绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller会创建临时文件夹并定义_MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    icon_path = resource_path("icon.ico")
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.setWindowIcon(QIcon(icon_path))
    player.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
