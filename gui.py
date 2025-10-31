import sys
import os
import ast
import re
from artifact import *
from analyze import *
from rank import rank_value
#from rank import *
from PySide6.QtWidgets import (QMainWindow, QApplication, QFileDialog, QLabel)
from PySide6.QtGui import (QIcon, QPixmap, QFont) # TODO: Pretty sure this is bad practice, and should instead subclass MainWindow
#from PySide6 import QtCore
#from PySide6.QtCore import (QSize)
#from PySide6 import QtWidgets

from MainWindow import Ui_MainWindow
from square_widget import SquareToolButton, SquareLabel
import resources

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.targetLine.setText('Enter optimization target')

        # Define and Reshape
        self.calcTargetButton.clicked.connect(self.resinCalculate)

        # Scan
        self.mainBrowseButton.clicked.connect(self.getMainFileName)
        self.extraBrowseButton.clicked.connect(self.getExtraFileNames)
        self.calcScanButton.clicked.connect(self.scanCalculate)
        
        self.statusbar.showMessage('Awaiting scan')
        
        self.mainScan = None
        self.extraScans = None
        self.artifact_dicts = None
        self.artifacts = None
        self.base_artifacts = None
        self.slots = None
        self.rarities = None
        self.slvls = None
        self.unactivated = None
        self.sets = None
        self.set_key = None
        self.target = None
        self.relevant = None
        
        self.mainTooltip.setPixmap(QPixmap(':/menu/icons/info.svg'))
        self.mainTooltip.setScaledContents(True)
        self.mainTooltip.setFixedSize(15, 15)
        
        self.extraTooltip.setPixmap(QPixmap(':/menu/icons/info.svg'))
        self.extraTooltip.setScaledContents(True)
        self.extraTooltip.setFixedSize(15, 15)
        
        self.upgradeArtifactImage = SquareLabel()
        self.upgradeArtifactInfo.insertWidget(0, self.upgradeArtifactImage)
        
        self.lockArtifactImage = SquareLabel()
        self.lockArtifactInfo.insertWidget(0, self.lockArtifactImage)
        #self.artifactInfo.setStretch()

    def getMainFileName(self):
        file_filter = 'GOOD JSON File (*.json)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select main scan', 
            dir=os.getcwd(),
            filter=file_filter,
            selectedFilter=file_filter
        )
        self.mainScan = response[0]
        self.mainFilepathLine.setText(self.mainScan)
        
    # TODO: implement multiple extra scans
    def getExtraFileNames(self):
        file_filter = 'GOOD JSON File (*.json)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select additional scans', 
            dir=os.getcwd(),
            filter=file_filter,
            selectedFilter=file_filter
        )
        self.extraScans = response[0]
        self.extraFilepathLine.setText(str(self.extraScans))
        
    # TODO: have a 'Save merged' button that appears if extra files are
    # selected
    
    def scanCalculate(self):
        if self.mainScan is None:
            self.statusbar.showMessage('Input a scan first', 10000)
            return
        # TODO: this mesage doesn't work, likely a thread issue with GIL
        self.statusbar.showMessage('Calculating...')
        (
            self.artifact_dicts, 
            self.artifacts, 
            self.base_artifacts, 
            self.slots, 
            self.rarities, 
            self.slvls, 
            self.unactivated, 
            self.sets
        ) = load(self.mainScan) if self.extraScans is None else merge_scans(self.mainScan, self.extraScans)
        
        self.artifact_mask = np.zeros(len(self.artifact_dicts), dtype=bool)
        for i, artifact in enumerate(self.artifact_dicts):
            self.artifact_mask[i] = artifact['rarity'] == 5 and not artifact['astralMark']
        
        relevance, counts = rate(self.artifacts, self.slots, self.artifact_mask, self.slvls, self.sets, rank_value, k=2)
        self.upgrade_mask = upgrade_analyze(relevance, counts, self.artifact_mask, self.slvls, num=20)
        self.delete_mask = delete_analyze(relevance, self.artifact_mask, num=100)
        self.statusbar.showMessage('Done', 10000)
        self.populate_upgrade()
        self.populate_lock()
        
    def resinCalculate(self):
        if self.artifacts is None:
            self.statusbar.showMessage('Process a scan first', 10000)
            return
        
        raw_set = self.setCombo.currentText()
        if raw_set == 'Set':
            self.statusbar.showMessage('Choose a set first', 10000)
            return
        
        self.set_key = raw_set.replace('-', ' ')
        self.set_key = re.sub(r'[^A-Za-z\s]', '', self.set_key)
        self.set_key = self.set_key.title()
        self.set_key = self.set_key.replace(' ', '')
        self.set_key = SET_2_NUM[self.set_key]
        
        # TODO: literal_eval makes me nervous, think of a more elegant
        # solution
        try:
            self.target = vectorize(ast.literal_eval(self.targetLine.text()))
        except:
            self.statusbar.showMessage('Improperly formatted optimization target', 10000)
            return
        
        resin_params = (
            self.artifacts,
            self.slots,
            self.rarities,
            self.slvls,
            self.sets,
            self.set_key,
            self.target
        )
        
        resin_0 = set_resin(*resin_params, improvement=0.0)
        resin_1 = set_resin(*resin_params, improvement=0.01)
        resin_5 = set_resin(*resin_params, improvement=0.05)
        
        resin_text = [f'If farming domains until an improvement\n']
        for i, slot_resin in enumerate(resin_0):
            if slot_resin == math.inf:
                resin_text.append(f'{SLOTS[i]}: ∞ resin, improvement is not possible')
            else:
                resin_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
        resin_text.append(f'\nIf farming domains until an improvement of at least 1%\n')
        for i, slot_resin in enumerate(resin_1):
            if slot_resin == math.inf:
                resin_text.append(f'{SLOTS[i]}: ∞ resin, 1% improvement is not possible')
            else:
                resin_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
        resin_text.append(f'\nIf farming domains until an improvement of at least 5%\n')
        for i, slot_resin in enumerate(resin_5):
            if slot_resin == math.inf:
                resin_text.append(f'{SLOTS[i]}: ∞ resin, 5% improvement is not possible')
            else:
                resin_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
        self.resinBox.setText('\n'.join(resin_text))
        
        reshape_params = (
            self.artifacts,
            self.base_artifacts,
            self.slots,
            self.rarities,
            self.slvls,
            self.unactivated,
            self.sets,
            self.set_key,
            self.target
        )
        
        reshape_resin_0 = set_reshape_resin(*reshape_params, improvement=0.0)
        reshape_resin_1 = set_reshape_resin(*reshape_params, improvement=0.01)
        reshape_resin_5 = set_reshape_resin(*reshape_params, improvement=0.05)
        
        reshape_text = [f'If reshaping instead of farming until an improvement, each Dust of Enlightenment saves an average of\n']
        for i, (slot_resin, artifact_idx) in enumerate(reshape_resin_0):
            if slot_resin == math.inf:
                reshape_text.append(f'{SLOTS[i]}: ∞ resin, improvement is not possible')
            else:
                reshape_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
            print_artifact_dict(self.artifact_dicts[artifact_idx])
        reshape_text.append(f'\nIf reshaping instead of farming until an improvement of at least 1%, each Dust of Enlightenment saves an average of\n')
        for i, (slot_resin, artifact_idx) in enumerate(reshape_resin_1):
            if slot_resin == math.inf:
                reshape_text.append(f'{SLOTS[i]}: ∞ resin, 1% improvement is not possible')
            else:
                reshape_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
            print_artifact_dict(self.artifact_dicts[artifact_idx])
        reshape_text.append(f'\nIf reshaping instead of farming until an improvement of at least 5%, each Dust of Enlightenment saves an average of\n')
        for i, (slot_resin, artifact_idx) in enumerate(reshape_resin_5):
            if slot_resin == math.inf:
                reshape_text.append(f'{SLOTS[i]}: ∞ resin, 5% improvement is not possible')
            else:
                reshape_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
            print_artifact_dict(self.artifact_dicts[artifact_idx])
        self.reshapeBox.setText('\n'.join(reshape_text))
        
        define_params = (
            self.artifacts,
            self.slots,
            self.rarities,
            self.slvls,
            self.sets,
            self.set_key,
            self.target
        )
        
        define_resin_0 = set_define_resin(*define_params, improvement=0.0)
        define_resin_1 = set_define_resin(*define_params, improvement=0.01)
        define_resin_5 = set_define_resin(*define_params, improvement=0.05)
        
        define_text = [f'If defining instead of farming until an improvement, each Sanctifying Elixir saves an average of\n']
        for i, slot_resin in enumerate(define_resin_0):
            if slot_resin == math.inf:
                define_text.append(f'{SLOTS[i]}: ∞ resin, improvement is not possible')
            else:
                define_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
        define_text.append(f'\nIf defining instead of farming until an improvement of at least 1%, each Sanctifying Elixir saves an average of\n')
        for i, slot_resin in enumerate(define_resin_1):
            if slot_resin == math.inf:
                define_text.append(f'{SLOTS[i]}: ∞ resin, 1% improvement is not possible')
            else:
                define_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
        define_text.append(f'\nIf defining instead of farming until an improvement of at least 5%, each Sanctifying Elixir saves an average of\n')
        for i, slot_resin in enumerate(define_resin_5):
            if slot_resin == math.inf:
                define_text.append(f'{SLOTS[i]}: ∞ resin, 5% improvement is not possible')
            else:
                define_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days')
        self.defineBox.setText('\n'.join(define_text))
        
    def populate_upgrade(self):
        grid = self.upgradeGrid
        while grid.count():
            w = grid.itemAt(0).widget()
            if w:
                grid.removeWidget(w)
                w.deleteLater()
                
        if self.artifact_dicts is None:
            raise ValueError('This should not be possible')
        
        NUM_COLS = 8
        
        for i, artifact in enumerate(self.artifact_dicts):
            row, col = divmod(i, NUM_COLS)
            
            button = SquareToolButton()
            if self.upgrade_mask[i]:
                # Incorrectly locked
                icon_path = f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'
                button.clicked.connect(lambda _, idx=i: self.click_upgrade_artifact(idx))
            else:
                # Correctly locked
                icon_path = f':/{artifact['slotKey']}_icons/default.webp'
            button.setIcon(QIcon(icon_path))
            grid.addWidget(button, row, col)
    
    def populate_lock(self):
        grid = self.lockGrid
        while grid.count():
            w = grid.itemAt(0).widget()
            if w:
                grid.removeWidget(w)
                w.deleteLater()
                
        if self.artifact_dicts is None:
            raise ValueError('This should not be possible')
        
        NUM_COLS = 8
        
        for i, artifact in enumerate(self.artifact_dicts):
            row, col = divmod(i, NUM_COLS)
            
            button = SquareToolButton()
            if self.delete_mask[i] == artifact['lock']:
                # Incorrectly locked
                icon_path = f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'
                button.clicked.connect(lambda _, idx=i: self.click_lock_artifact(idx))
            else:
                # Correctly locked
                icon_path = f':/{artifact['slotKey']}_icons/default.webp'
            button.setIcon(QIcon(icon_path))
            grid.addWidget(button, row, col)
            
    def click_upgrade_artifact(self, idx):
        artifact = self.artifact_dicts[idx]
        self.upgradeArtifactImage.setPixmap(QPixmap(f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'))
        self.upgradeArtifactMain.setText(artifact['mainStatKey'])
        self.upgradeArtifactLvl.setText(f'+{artifact['level']}')
        substats = artifact['substats']
        # TODO: make this more dynamic instead of hardcoding 3/4
        # substats and 0/1 unactivated substats
        self.upgradeArtifactSub1.setText(f'{substats[0]['key']}+{substats[0]['value']}')
        self.upgradeArtifactSub2.setText(f'{substats[1]['key']}+{substats[1]['value']}')
        self.upgradeArtifactSub3.setText(f'{substats[2]['key']}+{substats[2]['value']}')
        if len(substats) == 4:
            self.upgradeArtifactSub4.setText(f'{substats[3]['key']}+{substats[3]['value']}')
        else:
            substat = artifact['unactivatedSubstats'][0]
            self.upgradeArtifactSub4.setText(f'{substat['key']}+{substat['value']} (unactivated)')
        self.upgradeArtifactSet.setText(artifact['setKey'])
        if artifact['lock']:
            self.upgradeLock.setPixmap(QPixmap(':/menu/icons/locked.svg'))
        else:
            self.upgradeLock.setPixmap(QPixmap(':/menu/icons/unlocked.svg'))
        self.upgradeLock.setScaledContents(True)
        self.upgradeLock.setFixedSize(35, 35)
        if artifact['astralMark']:
            self.upgradeStar.setPixmap(QPixmap(':/menu/icons/star.svg'))
        else:
            self.upgradeStar.setPixmap(QPixmap(':/menu/icons/unstar.svg'))
        self.upgradeStar.setScaledContents(True)
        self.upgradeStar.setFixedSize(35, 35)
    
    def click_lock_artifact(self, idx):
        artifact = self.artifact_dicts[idx]
        self.lockArtifactImage.setPixmap(QPixmap(f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'))
        self.lockArtifactMain.setText(artifact['mainStatKey'])
        self.lockArtifactLvl.setText(f'+{artifact['level']}')
        substats = artifact['substats']
        # TODO: make this more dynamic instead of hardcoding 3/4
        # substats and 0/1 unactivated substats
        self.lockArtifactSub1.setText(f'{substats[0]['key']}+{substats[0]['value']}')
        self.lockArtifactSub2.setText(f'{substats[1]['key']}+{substats[1]['value']}')
        self.lockArtifactSub3.setText(f'{substats[2]['key']}+{substats[2]['value']}')
        if len(substats) == 4:
            self.lockArtifactSub4.setText(f'{substats[3]['key']}+{substats[3]['value']}')
        else:
            substat = artifact['unactivatedSubstats'][0]
            self.lockArtifactSub4.setText(f'{substat['key']}+{substat['value']} (unactivated)')
        self.lockArtifactSet.setText(artifact['setKey'])
        if artifact['lock']:
            # Should unlock
            self.lockLock.setPixmap(QPixmap(':/menu/icons/unlocked.svg'))
        else:
            # Should lock
            self.lockLock.setPixmap(QPixmap(':/menu/icons/locked.svg'))
        self.lockLock.setScaledContents(True)
        self.lockLock.setFixedSize(35, 35)
        if artifact['astralMark']:
            raise ValueError
            self.lockStar.setPixmap(QPixmap(':/menu/icons/star.svg'))
        else:
            self.lockStar.setPixmap(QPixmap(':/menu/icons/unstar.svg'))
        self.lockStar.setScaledContents(True)
        self.lockStar.setFixedSize(35, 35)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(11)
    app.setFont(font)

    window = MainWindow()
    window.show()
    app.exec()