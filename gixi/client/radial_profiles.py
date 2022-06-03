import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSlot


class RadialProfilesWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.q_max = np.sqrt(2) * 3.2

        self.radial_plot = self.addPlot(title='Radial Profiles')
        self.radial_plot.addLegend()
        plot = self.radial_plot
        self.measured = plot.plot([], pen=(0, 0, 200), name='Measured')
        self.fitted = plot.plot([], pen=(0, 128, 0), name='Fitted')
        self.cif = plot.plot([], pen=(19, 234, 201), name='')

    @pyqtSlot(dict)
    def set_data(self, data: dict):
        self.measured.setData(data['q'], data['measured_profile'])
        self.fitted.setData(data['q'], data['fitted_profile'])

    @pyqtSlot()
    def clear_data(self):
        self.measured.setData([])
        self.fitted.setData([])

    @pyqtSlot(dict)
    def set_cif_profile(self, cif_data: dict):
        self.cif.setData(cif_data['q'], cif_data['profile'])
        self.radial_plot.legend.removeItem(self.cif)
        self.radial_plot.legend.update()
        self.radial_plot.legend.addItem(self.cif, cif_data['name'])
