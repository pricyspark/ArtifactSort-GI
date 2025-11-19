from PySide6.QtCharts import QChartView
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QToolTip, QLabel
from PySide6.QtCore import Qt, QPoint

class ChartTip(QLabel):
    offset = QPoint(12, 12)
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip)        # looks like a tooltip
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: #ffffe1; border: 1px solid gray; padding: 3px;")
        self.hide()

    def show_at(self, global_pos: QPoint, text: str):
        self.setText(text)
        self.adjustSize()
        self.move(global_pos + ChartTip.offset)
        self.show()

class HoverChartView(QChartView):
    def __init__(self, chart, series_list, parent=None):
        super().__init__(chart, parent)
        self.series_list = series_list
        self.setMouseTracking(True)
        self.tip = ChartTip(self)
        
        series = self.series_list[0][1]
        first = series.at(0).x()
        last = series.at(series.count() - 1).x()
        self.num_points = series.count()
        
        self.range = last - first
        self.offset = first
        
        # TODO: when hovering over the right side of the chart, the
        # tooltip goes offscreen
        
    def mouseMoveEvent(self, event):
        chart = self.chart()
        plot_area = chart.plotArea()

        scene_pos = self.mapToScene(event.pos())
        if not plot_area.contains(scene_pos):
            #QToolTip.hideText()
            self.tip.hide()
            return super().mouseMoveEvent(event)

        value_pos = chart.mapToValue(scene_pos, self.series_list[0][1])
        x = value_pos.x()

        lines = [f'{x:.0f}% improvement']

        # Assumes evenly spaced points
        percent = min(max(0, x - self.offset) / self.range, 1)    
        closest = round(percent * (self.num_points - 1))
        for name, series in self.series_list:
            if series.count() <= closest:
                continue
            p = series.at(closest)
            lines.append(f'{name}: {round(p.y())} resin, {round(p.y() / 180)} days')

        text = "\n".join(lines)
        #QToolTip.showText(event.globalPos(), text, msecShowTime=100000)
        self.tip.show_at(event.globalPos(), text)

        super().mouseMoveEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        
        series = self.series_list[0][1]
        first = series.at(0).x()
        last = series.at(series.count() - 1).x()
        
        self.range = last - first
        self.offset = first
        
        return super().resizeEvent(event)