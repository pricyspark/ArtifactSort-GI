from PySide6.QtWidgets import QToolButton, QSizePolicy, QLabel, QVBoxLayout
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont

font1 = QFont()
font1.setPointSize(20)
font2 = QFont()
font2.setPointSize(15)

class ArtifactFullWidget(QVBoxLayout):
    def __init__(self, parent=None) -> None:
        raise NotImplementedError
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)
    
class ArtifactLiteWidget(QVBoxLayout):
    def __init__(self, parent=None) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)
            
        self.main = QLabel('')
        self.subs = [QLabel('') for _ in range(4)]
        
        self.main.setFont(font1)
        self.main.setWordWrap(True)
        self.main.setMargin(5)
        self.addWidget(self.main)
        for sub in self.subs:
            sub.setFont(font2)
            sub.setWordWrap(True)
            sub.setMargin(5)
            self.addWidget(sub)
        
    def setText(self, artifact: dict) -> None:
        self.main.setText(artifact['mainStatKey'])
        substats = artifact['substats']
        unactivated = artifact['unactivatedSubstats']
        for i, substat in enumerate(substats):
            value = substat['value']
            text = f'{substat['key']}+{substat['value']}' if value else substat['key']
            self.subs[i].setText(text)
        for i, substat in enumerate(unactivated):
            value = substat['value']
            text = f'{substat['key']}+{substat['value']} (unactivated)' if value else f'{substat['key']} (unactivated)'
            self.subs[i].setText(text)
            
    def clear(self) -> None:
        self.main.setText('')
        for sub in self.subs:
            sub.setText('')