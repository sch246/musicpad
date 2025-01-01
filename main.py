import sys
from PyQt6.QtWidgets import QApplication
from musicpad import AudioPlayer


def main():
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
