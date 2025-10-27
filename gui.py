import sys
import os
import ast
import re
from artifact import *
from analyze import *
from rank import rank_value
#from rank import *
from PySide6.QtWidgets import (QMainWindow, QApplication, QFileDialog, QStatusBar)
#from PySide6 import QtWidgets

from MainWindow import Ui_MainWindow

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
        
        relevant = rate(self.artifacts, self.slots, self.rarities, self.slvls, self.sets, rank_value, k=2, num=100)
        self.statusbar.showMessage('Done')
        visualize(relevant, self.artifact_dicts)
        
    def resinCalculate(self):
        if self.artifacts is None:
            self.statusbar.showMessage('Input a scan first', 10000)
            return
        
        # TODO: literal_eval makes me nervous, think of a more elegant
        # solution
        raw_set = self.setCombo.currentText()
        if raw_set == 'Set':
            self.statusbar.showMessage('Choose a set first', 10000)
            return
        
        self.set_key = raw_set.replace('-', ' ')
        self.set_key = re.sub(r'[^A-Za-z\s]', '', self.set_key)
        self.set_key = self.set_key.title()
        self.set_key = self.set_key.replace(' ', '')
        self.set_key = SET_2_NUM[self.set_key]
        
        try:
            self.target = vectorize(ast.literal_eval(self.targetLine.text()))
        except:
            self.statusbar.showMessage('Improperly formatted optimization target', 10000)
            return
        
        # TODO: add an input for improvement, or show levels by default    
        improvement = 0.0
        
        resin = set_resin(
            self.artifacts,
            self.slots,
            self.rarities,
            self.slvls,
            self.sets,
            self.set_key,
            self.target,
            improvement=improvement
        )
        
        reshape_resin = set_reshape_resin(
            self.artifacts, 
            self.base_artifacts,
            self.slots,
            self.rarities,
            self.slvls,
            self.unactivated,
            self.sets,
            self.set_key,
            self.target,
            improvement=improvement
        )
        
        define_resin = set_define_resin(
            self.artifacts,
            self.slots,
            self.rarities,
            self.slvls,
            self.sets,
            self.set_key,
            self.target,
            improvement=improvement
        )
        
        resin_text = [f'If farming domains until an improvement of >{improvement * 100}%\n']
        for i, slot_resin in enumerate(resin):
            if slot_resin == math.inf:
                resin_text.append(f'{SLOTS[i]}: ∞ resin, {100 * 0}% improvement is not possible\n')
            else:
                resin_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days\n')       
        self.resinBox.setText('\n'.join(resin_text))
        
        reshape_text = [f'If reshaping instead of farming, each Dust of Enlightenment saves an average of\n']
        for i, (slot_resin, artifact_idx) in enumerate(reshape_resin):
            if slot_resin == math.inf:
                reshape_text.append(f'{SLOTS[i]}: ∞ resin, {100 * improvement}% improvement is not possible\n')
            else:
                reshape_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days\n')
            print_artifact_dict(self.artifact_dicts[artifact_idx])
        self.reshapeBox.setText('\n'.join(reshape_text))
        
        define_text = [f'If defining instead of farming, each Sanctifying Elixir saves an average of\n']
        for i, slot_resin in enumerate(define_resin):
            if slot_resin == math.inf:
                define_text.append(f'{SLOTS[i]}: ∞ resin, {100 * improvement}% improvement is not possible\n')
            else:
                define_text.append(f'{SLOTS[i]}: {slot_resin} resin, {math.ceil(slot_resin / 180)} days\n')
        self.defineBox.setText('\n'.join(define_text))

app = QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()