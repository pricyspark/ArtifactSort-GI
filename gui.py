import sys
import os
import ast
import re
import time
from artifact import *
from PySide6.QtWidgets import (QMainWindow, QApplication, QFileDialog, QLabel, QDialog, QSpinBox)
from PySide6.QtGui import (QIcon, QPixmap, QFont) # TODO: Pretty sure this is bad practice, and should instead subclass MainWindow
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QLogValueAxis
#from PySide6 import QtCore
#from PySide6.QtCore import (QSize)
#from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from MainWindow import Ui_MainWindow
from TargetDialog import Ui_Dialog
from square_widget import SquareToolButton, SquareLabel
from chart import HoverChartView
import resources

# TODO: handling each stat as a seperate QLabel is super verbose and
# terrible. At some point, stop being a lazy idiot

def _substat_text(artifact_dict: dict, index: int) -> str:
    substats = artifact_dict['substats']
    return f'{substats[index]['key']}+{substats[index]['value']}'

def _clear_layout(layout) -> None:
    while layout.count() > 0:
        widget = layout.takeAt(0).widget()
        if widget is not None:
            widget.deleteLater()

class TargetDialog(QDialog, Ui_Dialog):
    def __init__(self, weights = None) -> None:
        super().__init__()
        self.setupUi(self)
        
        for row in range(self.tableWidget.rowCount()):
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(100) # WARNING: I think this is big enough to overflow score if everything is set to 100
            self.tableWidget.setCellWidget(row, 0, spin)
        
        if weights is None:
            return
        
        for i, weight in enumerate(weights):
            cell = self.tableWidget.cellWidget(i, 0)
            assert isinstance(cell, QSpinBox)
            cell.setValue(weight)
        
    def get_values(self) -> list[int]:
        values = []
        for row in range(self.tableWidget.rowCount()):
            cell = self.tableWidget.cellWidget(row, 0)
            assert isinstance(cell, QSpinBox)
            values.append(cell.value())
            
        return values

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        
        # Define and Reshape
        self.calcTargetButton.clicked.connect(self.resinCalculate)
        self.targetButton.clicked.connect(self.openTargetDialog)

        # Scan
        self.mainBrowseButton.clicked.connect(self.getMainFileName)
        self.extraBrowseButton.clicked.connect(self.getExtraFileNames)
        self.calcScanButton.clicked.connect(self.scanCalculate)
        
        self.statusbar.showMessage('Awaiting scan')
        
        self.mainScan: str | None = None
        self.extraScans: str | None = None
        self.artifact_dicts: dict | None = None
        self.artifacts: NDArray[ARTIFACT_DTYPE] | None = None
        self.base_artifacts: NDArray[ARTIFACT_DTYPE] | None = None
        self.slots: NDArray[np.uint8] | None = None
        self.rarities: NDArray[np.uint8] | None = None
        self.lvls: NDArray[LVL_DTYPE] | None = None
        self.slvls: NDArray[SLVL_DTYPE] | None = None
        self.unactivated: NDArray[np.bool] | None = None
        self.sets: NDArray[np.unsignedinteger] | None = None
        self.set_key: int | None = None
        self.target: NDArray[TARGET_DTYPE] | None = None
        self.relevant: NDArray[np.bool] | None = None
        
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
        
        # Clear charts, if they exist
        flower_layout = self.flowerContainer.layout()
        plume_layout = self.plumeContainer.layout()
        sands_layout = self.sandsContainer.layout()
        goblet_layout = self.gobletContainer.layout()
        circlet_layout = self.circletContainer.layout()
        
        assert flower_layout is not None
        assert plume_layout is not None
        assert sands_layout is not None
        assert goblet_layout is not None
        assert circlet_layout is not None
        
        _clear_layout(flower_layout)
        _clear_layout(plume_layout)
        _clear_layout(sands_layout)
        _clear_layout(goblet_layout)
        _clear_layout(circlet_layout)
        
        # Clear artifacts
        self.flowerBestSub1.setText('')
        self.flowerBestSub2.setText('')
        self.flowerBestSub3.setText('')
        self.flowerBestSub4.setText('')
        self.flowerReshapeMain.setText('')
        self.flowerReshapeSub1.setText('')
        self.flowerReshapeSub2.setText('')
        self.flowerReshapeSub3.setText('')
        self.flowerReshapeSub4.setText('')
        self.plumeBestSub1.setText('')
        self.plumeBestSub2.setText('')
        self.plumeBestSub3.setText('')
        self.plumeBestSub4.setText('')
        self.plumeReshapeMain.setText('')
        self.plumeReshapeSub1.setText('')
        self.plumeReshapeSub2.setText('')
        self.plumeReshapeSub3.setText('')
        self.plumeReshapeSub4.setText('')
        self.sandsBestSub1.setText('')
        self.sandsBestSub2.setText('')
        self.sandsBestSub3.setText('')
        self.sandsBestSub4.setText('')
        self.sandsReshapeMain.setText('')
        self.sandsReshapeSub1.setText('')
        self.sandsReshapeSub2.setText('')
        self.sandsReshapeSub3.setText('')
        self.sandsReshapeSub4.setText('')
        self.gobletBestSub1.setText('')
        self.gobletBestSub2.setText('')
        self.gobletBestSub3.setText('')
        self.gobletBestSub4.setText('')
        self.gobletReshapeMain.setText('')
        self.gobletReshapeSub1.setText('')
        self.gobletReshapeSub2.setText('')
        self.gobletReshapeSub3.setText('')
        self.gobletReshapeSub4.setText('')
        self.circletBestSub1.setText('')
        self.circletBestSub2.setText('')
        self.circletBestSub3.setText('')
        self.circletBestSub4.setText('')
        self.circletReshapeMain.setText('')
        self.circletReshapeSub1.setText('')
        self.circletReshapeSub2.setText('')
        self.circletReshapeSub3.setText('')
        self.circletReshapeSub4.setText('')
        
        (
            self.artifact_dicts, 
            self.artifacts, 
            self.base_artifacts, 
            self.slots, 
            self.rarities, 
            self.lvls,
            self.slvls, 
            self.unactivated, 
            self.sets
        ) = load(self.mainScan) if self.extraScans is None else merge_scans(self.mainScan, self.extraScans)
        
        self.artifact_mask = np.zeros(len(self.artifact_dicts), dtype=bool)
        for i, artifact in enumerate(self.artifact_dicts):
            if 'astralMark' in artifact:
                self.artifact_mask[i] = artifact['rarity'] == 5 and not artifact['astralMark']
            else:
                # TODO: warn no astral mark. Say which scanner didn't.
                self.artifact_mask[i] = artifact['rarity'] == 5
        
        relevance, counts = rate(self.artifacts, self.slots, self.artifact_mask, self.slvls, self.sets, rank_value, k=2)
        self.upgrade_mask = upgrade_analyze(relevance, counts, self.artifact_mask, self.slvls, num=20)
        start = time.perf_counter()
        relevance, counts = delete_rate(self.artifacts, self.slots, self.artifact_mask, self.slvls, self.sets)
        self.delete_mask = delete_analyze(relevance, counts, self.artifact_mask, num=100)
        end = time.perf_counter()
        print(end - start)
        self.statusbar.showMessage('Done', 10000)
        self.populate_upgrade()
        self.populate_lock()
        
    def openTargetDialog(self):
        try:
            target = vectorize(ast.literal_eval(self.targetLine.text()))
            # TODO: make sure input weight is a natural number and they
            # sum to <=400. This makes sure score fits in uint16. Maybe
            # use uint32 and the range becomes <=26000000
            
        except:
            self.statusbar.showMessage('Improperly formatted optimization target', 10000)
            target = None
        dialog = TargetDialog(target)
        if dialog.exec():
            self.targetLine.setText(str(unvectorize(dialog.get_values())))
        
    def resinCalculate(self):
        if self.artifacts is None:
            self.statusbar.showMessage('Process a scan first', 10000)
            return
        
        assert self.artifact_dicts is not None
        assert self.base_artifacts is not None
        assert self.slots is not None
        assert self.rarities is not None
        assert self.lvls is not None
        assert self.unactivated is not None
        assert self.sets is not None
        raw_set = self.setCombo.currentText()
        # TODO: reorder sets to match combobox and use currentIndex()
        if raw_set == 'Set':
            self.statusbar.showMessage('Choose a set first', 10000)
            return
        
        set_key = raw_set.replace('-', ' ')
        set_key = re.sub(r'[^A-Za-z\s]', '', set_key)
        set_key = set_key.title()
        set_key = set_key.replace(' ', '')
        self.set_key = SET_2_NUM[set_key]
        
        # TODO: literal_eval makes me nervous, think of a more elegant
        # solution
        try:
            self.target = vectorize(ast.literal_eval(self.targetLine.text()))
            # TODO: make sure input weight is a natural number and they
            # sum to <=400. This makes sure score fits in uint16. Maybe
            # use uint32 and the range becomes <=26000000
        except:
            self.statusbar.showMessage('Improperly formatted optimization target', 10000)
            return
        
        def resin_chart(container, resin_points, maximum) -> None:
            resin_series = QLineSeries()
            resin_series.setName('Resin')
            for i, resin in enumerate(resin_points[1]):
                resin_series.append(i, resin)
                
            define_series = QLineSeries()
            define_series.setName('Define')
            for i, resin in enumerate(resin_points[2]):
                define_series.append(i, resin)
                
            reshape_series = QLineSeries()
            reshape_series.setName('Reshape')
            for i, resin in enumerate(resin_points[3]):
                reshape_series.append(i, resin[0])
            
            chart = QChart()
            chart.addSeries(resin_series)
            chart.addSeries(define_series)
            chart.addSeries(reshape_series)
            
            x_axis = QValueAxis()
            x_axis.setTitleText('Improvement (%)')
            x_axis.setRange(0, len(resin_points[1]) - 1)
            chart.addAxis(x_axis, Qt.AlignBottom)
            resin_series.attachAxis(x_axis)
            define_series.attachAxis(x_axis)
            reshape_series.attachAxis(x_axis)
            
            y_axis = QLogValueAxis()
            y_axis.setTitleText('Resin')
            y_axis.setRange(1, maximum)
            y_axis.setLabelFormat('%.0e')
            chart.addAxis(y_axis, Qt.AlignLeft)
            resin_series.attachAxis(y_axis)
            define_series.attachAxis(y_axis)
            reshape_series.attachAxis(y_axis)
            
            view = HoverChartView(
                chart,
                [
                    ("Resin", resin_series),
                    ("Define", define_series),
                    ("Reshape", reshape_series),
                ],
            )
            layout = container.layout()
            assert layout is not None
            _clear_layout(layout)            
            layout.addWidget(view)
            
        range_params = (
            self.artifacts,
            self.base_artifacts,
            self.slots,
            self.rarities,
            self.lvls,
            self.unactivated,
            self.sets,
            self.set_key,
            self.target
        )
        
        flower_points = range_resin(*range_params, 'flower')
        if flower_points[0] < 0:
            self.flowerBestMain.setText('')
            if flower_points[0] == -1:
                self.flowerBestSub1.setText('No maxed 5* flower')
            else:
                self.flowerBestSub1.setText('All maxed 5* flowers have 0 score')
            self.flowerBestSub2.setText('')
            self.flowerBestSub3.setText('')
            self.flowerBestSub4.setText('')
            self.flowerReshapeMain.setText('')
            self.flowerReshapeSub1.setText('')
            self.flowerReshapeSub2.setText('')
            self.flowerReshapeSub3.setText('')
            self.flowerReshapeSub4.setText('')
        else:
            best_flower = self.artifact_dicts[flower_points[0]]
            self.flowerBestMain.setText(best_flower['mainStatKey'])
            self.flowerBestSub1.setText(_substat_text(best_flower, 0))
            self.flowerBestSub2.setText(_substat_text(best_flower, 1))
            self.flowerBestSub3.setText(_substat_text(best_flower, 2))
            self.flowerBestSub4.setText(_substat_text(best_flower, 3))
            try:
                reshape_flower = self.artifact_dicts[flower_points[3][0][1]] # temp. For now display the best for 0%
                self.flowerReshapeMain.setText(reshape_flower['mainStatKey'])
                self.flowerReshapeSub1.setText(_substat_text(reshape_flower, 0))
                self.flowerReshapeSub2.setText(_substat_text(reshape_flower, 1))
                self.flowerReshapeSub3.setText(_substat_text(reshape_flower, 2))
                self.flowerReshapeSub4.setText(_substat_text(reshape_flower, 3))
            except IndexError:
                self.flowerReshapeMain.setText('')
                self.flowerReshapeSub1.setText('Reshaping cannot improve flower')
                self.flowerReshapeSub2.setText('')
                self.flowerReshapeSub3.setText('')
                self.flowerReshapeSub4.setText('')
        
        plume_points = range_resin(*range_params, 'plume')
        if plume_points[0] < 0:
            self.plumeBestMain.setText('')
            if plume_points[0] == -1:
                self.plumeBestSub1.setText('No maxed 5* plume')
            else:
                self.plumeBestSub1.setText('All maxed 5* plumes have 0 score')
            self.plumeBestSub2.setText('')
            self.plumeBestSub3.setText('')
            self.plumeBestSub4.setText('')
            self.plumeReshapeMain.setText('')
            self.plumeReshapeSub1.setText('')
            self.plumeReshapeSub2.setText('')
            self.plumeReshapeSub3.setText('')
            self.plumeReshapeSub4.setText('')
        else:
            best_plume = self.artifact_dicts[plume_points[0]]
            self.plumeBestMain.setText(best_plume['mainStatKey'])
            self.plumeBestSub1.setText(_substat_text(best_plume, 0))
            self.plumeBestSub2.setText(_substat_text(best_plume, 1))
            self.plumeBestSub3.setText(_substat_text(best_plume, 2))
            self.plumeBestSub4.setText(_substat_text(best_plume, 3))
            try:
                reshape_plume = self.artifact_dicts[plume_points[3][0][1]]
                self.plumeReshapeMain.setText(reshape_plume['mainStatKey'])
                self.plumeReshapeSub1.setText(_substat_text(reshape_plume, 0))
                self.plumeReshapeSub2.setText(_substat_text(reshape_plume, 1))
                self.plumeReshapeSub3.setText(_substat_text(reshape_plume, 2))
                self.plumeReshapeSub4.setText(_substat_text(reshape_plume, 3))
            except IndexError:
                self.plumeReshapeMain.setText('')
                self.plumeReshapeSub1.setText('Reshaping cannot improve plume')
                self.plumeReshapeSub2.setText('')
                self.plumeReshapeSub3.setText('')
                self.plumeReshapeSub4.setText('')
        
        sands_points = range_resin(*range_params, 'sands')
        if sands_points[0] < 0:
            self.sandsBestMain.setText('')
            if sands_points[0] == -1:
                self.sandsBestSub1.setText('No maxed 5* sands')
            else:
                self.sandsBestSub1.setText('All maxed 5* sands have 0 score')
            self.sandsBestSub2.setText('')
            self.sandsBestSub3.setText('')
            self.sandsBestSub4.setText('')
            self.sandsReshapeMain.setText('')
            self.sandsReshapeSub1.setText('')
            self.sandsReshapeSub2.setText('')
            self.sandsReshapeSub3.setText('')
            self.sandsReshapeSub4.setText('')
        else:
            best_sands = self.artifact_dicts[sands_points[0]]
            self.sandsBestMain.setText(best_sands['mainStatKey'])
            self.sandsBestSub1.setText(_substat_text(best_sands, 0))
            self.sandsBestSub2.setText(_substat_text(best_sands, 1))
            self.sandsBestSub3.setText(_substat_text(best_sands, 2))
            self.sandsBestSub4.setText(_substat_text(best_sands, 3))
            try:
                reshape_sands = self.artifact_dicts[sands_points[3][0][1]]
                self.sandsReshapeMain.setText(reshape_sands['mainStatKey'])
                self.sandsReshapeSub1.setText(_substat_text(reshape_sands, 0))
                self.sandsReshapeSub2.setText(_substat_text(reshape_sands, 1))
                self.sandsReshapeSub3.setText(_substat_text(reshape_sands, 2))
                self.sandsReshapeSub4.setText(_substat_text(reshape_sands, 3))
            except IndexError:
                self.sandsReshapeMain.setText('')
                self.sandsReshapeSub1.setText('Reshaping cannot improve sands')
                self.sandsReshapeSub2.setText('')
                self.sandsReshapeSub3.setText('')
                self.sandsReshapeSub4.setText('')
        
        goblet_points = range_resin(*range_params, 'goblet')
        if goblet_points[0] < 0:
            self.gobletBestMain.setText('')
            if goblet_points[0] == -1:
                self.gobletBestSub1.setText('No maxed 5* goblet')
            else:
                self.gobletBestSub1.setText('All maxed 5* goblets have 0 score')
            self.gobletBestSub2.setText('')
            self.gobletBestSub3.setText('')
            self.gobletBestSub4.setText('')
            self.gobletReshapeMain.setText('')
            self.gobletReshapeSub1.setText('')
            self.gobletReshapeSub2.setText('')
            self.gobletReshapeSub3.setText('')
            self.gobletReshapeSub4.setText('')
        else:
            best_goblet = self.artifact_dicts[goblet_points[0]]
            self.gobletBestMain.setText(best_goblet['mainStatKey'])
            self.gobletBestSub1.setText(_substat_text(best_goblet, 0))
            self.gobletBestSub2.setText(_substat_text(best_goblet, 1))
            self.gobletBestSub3.setText(_substat_text(best_goblet, 2))
            self.gobletBestSub4.setText(_substat_text(best_goblet, 3))
            try:
                reshape_goblet = self.artifact_dicts[goblet_points[3][0][1]]
                self.gobletReshapeMain.setText(reshape_goblet['mainStatKey'])
                self.gobletReshapeSub1.setText(_substat_text(reshape_goblet, 0))
                self.gobletReshapeSub2.setText(_substat_text(reshape_goblet, 1))
                self.gobletReshapeSub3.setText(_substat_text(reshape_goblet, 2))
                self.gobletReshapeSub4.setText(_substat_text(reshape_goblet, 3))
            except IndexError:
                self.gobletReshapeMain.setText('')
                self.gobletReshapeSub1.setText('Reshaping cannot improve goblet')
                self.gobletReshapeSub2.setText('')
                self.gobletReshapeSub3.setText('')
                self.gobletReshapeSub4.setText('')
                
        
        circlet_points = range_resin(*range_params, 'circlet')
        if circlet_points[0] < 0:
            self.circletBestMain.setText('')
            if circlet_points[0] == -1:
                self.circletBestSub1.setText('No maxed 5* circlet')
            else:
                self.circletBestSub1.setText('All maxed 5* circlets have 0 score')
            self.circletBestSub2.setText('')
            self.circletBestSub3.setText('')
            self.circletBestSub4.setText('')
            self.circletReshapeMain.setText('')
            self.circletReshapeSub1.setText('')
            self.circletReshapeSub2.setText('')
            self.circletReshapeSub3.setText('')
            self.circletReshapeSub4.setText('')
        else:
            best_circlet = self.artifact_dicts[circlet_points[0]]
            self.circletBestMain.setText(best_circlet['mainStatKey'])
            self.circletBestSub1.setText(_substat_text(best_circlet, 0))
            self.circletBestSub2.setText(_substat_text(best_circlet, 1))
            self.circletBestSub3.setText(_substat_text(best_circlet, 2))
            self.circletBestSub4.setText(_substat_text(best_circlet, 3))
            try:
                reshape_circlet = self.artifact_dicts[circlet_points[3][0][1]]
                self.circletReshapeMain.setText(reshape_circlet['mainStatKey'])
                self.circletReshapeSub1.setText(_substat_text(reshape_circlet, 0))
                self.circletReshapeSub2.setText(_substat_text(reshape_circlet, 1))
                self.circletReshapeSub3.setText(_substat_text(reshape_circlet, 2))
                self.circletReshapeSub4.setText(_substat_text(reshape_circlet, 3))
            except IndexError:
                self.circletReshapeMain.setText('')
                self.circletReshapeSub1.setText('Reshaping cannot improve circlet')
                self.circletReshapeSub2.setText('')
                self.circletReshapeSub3.setText('')
                self.circletReshapeSub4.setText('')
            
        points = (flower_points, plume_points, sands_points, goblet_points, circlet_points)
        non_empty_points = [point for point in points if point[0] != -1]
        
        chart_containers = (
            self.flowerContainer, 
            self.plumeContainer, 
            self.sandsContainer, 
            self.gobletContainer, 
            self.circletContainer
        )
        
        # Handle this first to prevent max() from erroring
        if not non_empty_points: # If everything is empty
            for chart_container in chart_containers:
                _clear_layout(chart_container.layout())
            return
                    
        resin_max = max([point[1][-1] for point in non_empty_points if len(point[1])])
        
        # TODO: you can def make a function that dynamically creates
        # labels and assigns text for them instead of manually doing
        # this like an idiot. But I'm too lazy to figure that out with
        # PySide. This is comically stupid
        
        for chart_container, point in zip(chart_containers, points):
            if point[0] == -1 or len(points[1]) == 0:
                _clear_layout(chart_container.layout())
                continue
            if len(point[1]) == 0:
                continue
            
            resin_chart(chart_container, point, resin_max)
            
        #resin_chart(self.flowerContainer, flower_points, resin_max)
        #resin_chart(self.plumeContainer, plume_points, resin_max)
        #resin_chart(self.sandsContainer, sands_points, resin_max)
        #resin_chart(self.gobletContainer, goblet_points, resin_max)
        #resin_chart(self.circletContainer, circlet_points, resin_max)
        
    def populate_upgrade(self):
        grid = self.upgradeGrid
        while grid.count():
            first = grid.itemAt(0)
            assert first is not None # Not sure if this is the right way to shut up the type checker
            w = first.widget()
            if w:
                grid.removeWidget(w)
                w.deleteLater()
                
        if self.artifact_dicts is None:
            raise ValueError('This should not be possible')
        
        NUM_COLS = 8
        
        for i, artifact in enumerate(self.artifact_dicts):
            row, col = divmod(i, NUM_COLS)
            
            button = SquareToolButton()
            if not self.upgrade_mask[i] or not self.artifact_mask[i]:
                # Correctly locked
                icon_path = f':/{artifact['slotKey']}_icons/default.webp'
            else:
                # Incorrectly locked
                icon_path = f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'
                button.clicked.connect(lambda _, idx=i: self.click_upgrade_artifact(idx))
            button.setIcon(QIcon(icon_path))
            grid.addWidget(button, row, col)
    
    def populate_lock(self):
        grid = self.lockGrid
        while grid.count():
            first = grid.itemAt(0)
            assert first is not None # Not sure if this is the right way to shut up the type checker
            w = first.widget()
            if w:
                grid.removeWidget(w)
                w.deleteLater()
                
        if self.artifact_dicts is None:
            raise ValueError('This should not be possible')
        
        NUM_COLS = 8
        
        for i, artifact in enumerate(self.artifact_dicts):
            row, col = divmod(i, NUM_COLS)
            
            button = SquareToolButton()
            if self.delete_mask[i] != artifact['lock'] or not self.artifact_mask[i]:
                # Correctly locked or ignore
                icon_path = f':/{artifact['slotKey']}_icons/default.webp'
            else:
                # Incorrectly locked
                icon_path = f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'
                button.clicked.connect(lambda _, idx=i: self.click_lock_artifact(idx))
            button.setIcon(QIcon(icon_path))
            grid.addWidget(button, row, col)
            
    def click_upgrade_artifact(self, idx):
        assert self.artifact_dicts is not None
        artifact = self.artifact_dicts[idx]
        self.upgradeArtifactImage.setPixmap(QPixmap(f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'))
        self.upgradeArtifactMain.setText(artifact['mainStatKey'])
        self.upgradeArtifactLvl.setText(f'+{artifact['level']}')
        substats = artifact['substats']
        # TODO: make this more dynamic instead of hardcoding 3/4
        # substats and 0/1 unactivated substats
        self.upgradeArtifactSub1.setText(_substat_text(artifact, 0))
        self.upgradeArtifactSub1.setText(_substat_text(artifact, 1))
        self.upgradeArtifactSub2.setText(_substat_text(artifact, 2))
        if len(substats) == 4:
            self.upgradeArtifactSub4.setText(_substat_text(artifact, 3))
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
        if 'astralMark' not in artifact:
            return
        if artifact['astralMark']:
            self.upgradeStar.setPixmap(QPixmap(':/menu/icons/star.svg'))
        else:
            self.upgradeStar.setPixmap(QPixmap(':/menu/icons/unstar.svg'))
        self.upgradeStar.setScaledContents(True)
        self.upgradeStar.setFixedSize(35, 35)
    
    def click_lock_artifact(self, idx):
        assert self.artifact_dicts is not None
        artifact = self.artifact_dicts[idx]
        self.lockArtifactImage.setPixmap(QPixmap(f':/{artifact['slotKey']}_icons/{artifact['setKey']}.webp'))
        self.lockArtifactMain.setText(artifact['mainStatKey'])
        self.lockArtifactLvl.setText(f'+{artifact['level']}')
        substats = artifact['substats']
        # TODO: make this more dynamic instead of hardcoding 3/4
        # substats and 0/1 unactivated substats
        self.lockArtifactSub1.setText(_substat_text(artifact, 0))
        self.lockArtifactSub2.setText(_substat_text(artifact, 1))
        self.lockArtifactSub3.setText(_substat_text(artifact, 2))
        if len(substats) == 4:
            self.lockArtifactSub4.setText(_substat_text(artifact, 3))
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
        if 'astralMark' not in artifact:
            return
        if artifact['astralMark']:
            raise ValueError('This should not be possible. Starred artifacts should be ignored')
            self.lockStar.setPixmap(QPixmap(':/menu/icons/star.svg'))
        else:
            self.lockStar.setPixmap(QPixmap(':/menu/icons/unstar.svg'))
        self.lockStar.setScaledContents(True)
        self.lockStar.setFixedSize(35, 35)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("Platform:", app.platformName())
    font = app.font()
    font.setPointSize(11)
    app.setFont(font)

    window = MainWindow()
    window.show()
    app.exec()