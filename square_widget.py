from PySide6.QtWidgets import QToolButton, QSizePolicy, QLabel
from PySide6.QtCore import QSize, Qt

class SquareLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        self.setScaledContents(True)
        
    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return w

    def resizeEvent(self, e):
        #side = min(self.width(), self.height())
        side = self.width()
        #self.setPixmap(QSize(int(side * 0.9), int(side * 0.9)))
        super().resizeEvent(e)

class SquareToolButton(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        #self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        #self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return w

    def resizeEvent(self, e):
        #side = min(self.width(), self.height())
        side = self.width()
        self.setIconSize(QSize(int(side * 0.9), int(side * 0.9)))
        super().resizeEvent(e)
