from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QPoint
from functools import wraps


def mountFunc(obj, funcname, func):
    '''给对象函数后添加内容，如果没有函数，报错'''
    if not hasattr(obj, funcname):
        raise AttributeError(f"{obj} has no attribute {funcname}")
    original_func = getattr(obj, funcname)
    @wraps(original_func)
    def new_func(*args, **kwargs):
        res = original_func(*args, **kwargs)
        func(*args, **kwargs)
        return res
    setattr(obj, funcname, new_func)

class DraggableVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dragging_widget = None
        self.drag_start_index = -1
        self.fixed_widgets = []

    def setFixed(self, widget):
        '''设置固定的widget'''
        if widget in self.fixed_widgets:
            return
        self.fixed_widgets.append(widget)

    def setDraggable(self, widget):
        '''设置可拖拽的widget'''
        if widget in self.fixed_widgets:
            self.fixed_widgets.remove(widget)
        self._initWidget(widget)

    def _initWidget(self, widget:QWidget):
        widget.setAcceptDrops(True)
        mountFunc(widget, 'mousePressEvent', lambda e: self._handle_mouse_press(e, widget))
        mountFunc(widget,'mouseMoveEvent', lambda e: self._handle_mouse_move(e, widget))


    def _handle_mouse_press(self, event, widget):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_widget = widget
            self.drag_start_index = self.indexOf(widget)

    def _handle_mouse_move(self, event, widget):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if widget != self.dragging_widget:
            return

        # 获取鼠标当前位置对应的目标widget
        target_pos = widget.mapTo(widget.parent(), event.pos())
        target_widget = self._get_widget_at_position(target_pos)

        if target_widget and target_widget != widget:
            # 获取目标位置索引
            target_index = self.indexOf(target_widget)
            # 移动widget
            self.removeWidget(widget)
            self.insertWidget(target_index, widget)


    def _get_widget_at_position(self, pos: QPoint):
        """获取指定位置的widget"""
        for i in range(self.count()):
            widget = self.itemAt(i).widget()
            if widget and widget not in self.fixed_widgets and widget.geometry().contains(pos):
                return widget
        return None

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QRadioButton, QPushButton,QSlider,QButtonGroup, QFrame)
    class YourWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            # 创建可拖拽布局
            self.draggable_layout = DraggableVBoxLayout()

            # 创建一些测试用的widget
            for i in range(5):
                widget = QFrame()
                # 设置不同颜色
                widget.setStyleSheet(f"background-color: rgb({i*50}, {i*50}, {i*50});")
                if i==2:
                    widget.setStyleSheet(f"background-color: rgb(0, 255, 0);")
                    self.draggable_layout.addFixedWidget(widget)
                else:
                    self.draggable_layout.addDraggableWidget(widget)
                widget.setFrameStyle(QFrame.Shape.Box)
                widget.setMinimumHeight(50)
                # 使用add_draggable_widget方法添加widget

            # 设置布局
            container = QWidget()
            container.setLayout(self.draggable_layout)
            self.setCentralWidget(container)
    app = QApplication([])
    player = YourWindow()
    player.show()
    sys.exit(app.exec())
