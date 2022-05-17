from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import (QWidget, QPushButton, QButtonGroup, QFileDialog,
                             QHBoxLayout, QVBoxLayout, QApplication, QGroupBox, QRadioButton, 
                             QCheckBox, QLineEdit, QLabel, QSpinBox)
from PyQt5.QtGui import QDrag, QImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar 
import numpy as np

# https://www.mfitzp.com/tutorials/plotting-matplotlib/
# https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
class StrainCurvesCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)        
        # self.fig.tight_layout()        
        super(StrainCurvesCanvas, self).__init__(self.fig)

class StrainCurvesViewer(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self, strain_matrix):
        super().__init__()

        self.strain_matrix = strain_matrix        
        self.setWindowTitle('Strain Curve Viewer')
        self.init_UI()
        self.compute_strain_curves()
        self.plot()
        # layout = QVBoxLayout()
        # self.label = QLabel("Another Window" + str(strain_matrix.shape))
        # layout.addWidget(self.label)
        # self.setLayout(layout)
    
    def init_UI(self):
        
        # 1. Base layout: hbox
        baseHBox = QHBoxLayout()

        # 2. Left panel: annotation canvas
        annoVBox = QVBoxLayout()
        
        self.sc = StrainCurvesCanvas(self, width=10, height=4, dpi=100)
        toolbar = NavigationToolbar(self.sc, self)
        # self.setCentralWidget(toolbar)

        # layout = QtWidgets.QVBoxLayout()
        # layout.addWidget(toolbar)
        annoVBox.addWidget(self.sc)
        annoVBox.addWidget(toolbar)

        # Finish laft panel
        baseHBox.addLayout(annoVBox)

        # 3. Right Panel: settings and tools
        toolsVBox = QVBoxLayout() 
        toolsVBoxWidth = 150

        ## 3.1 Segment Amount
        segment_amount_group_box = QGroupBox("# of segments")
        segment_amount_group_layout = QVBoxLayout()
        self.segment_amount_LE = QLineEdit()
        self.segment_amount_LE.setText('6')
        self.segment_amount_LE.returnPressed.connect(self.segment_amount_LE_enter_predded) # refresh plot if press enter
        segment_amount_group_layout.addWidget(self.segment_amount_LE)
        segment_amount_group_box.setLayout(segment_amount_group_layout)
        segment_amount_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(segment_amount_group_box)

        ## 3.2 Subplot Options
        subplot_group_box = QGroupBox("Subplot Options")
        self.subplot_btn_box = QButtonGroup()
        self.radio_subplot = QRadioButton('Subplots');  self.radio_subplot.clicked.connect(self.subplot_button_toggled)
        self.radio_all = QRadioButton('All-in-one');    self.radio_all.clicked.connect(self.subplot_button_toggled)
        self.radio_subplot.setChecked(False);
        self.radio_all.setChecked(False);

        subplot_group_box_layout = QVBoxLayout()
        subplot_group_box_layout.addWidget(self.radio_subplot);self.subplot_btn_box.addButton(self.radio_subplot, 0)
        subplot_group_box_layout.addWidget(self.radio_all);self.subplot_btn_box.addButton(self.radio_all, 1)
        subplot_group_box.setLayout(subplot_group_box_layout)
        subplot_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(subplot_group_box)

        ## 3.4 Line Style
        line_style_group_box = QGroupBox("Line Style")
        line_style_group_layout = QVBoxLayout()
        line_width_label = QLabel()
        line_width_label.setText('Line width')
        line_style_group_layout.addWidget(line_width_label)

        self.line_width_sbox = QSpinBox()
        self.line_width_sbox.setValue(3)
        self.line_width_sbox.valueChanged.connect(self.plot)
        line_style_group_layout.addWidget(self.line_width_sbox)

        line_style_group_box.setLayout(line_style_group_layout)
        line_style_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(line_style_group_box)

        # QSpinBox
        ## 3.-1 Export to clipboard
        export_plot_cb_button = QPushButton()
        export_plot_cb_button.setText('Copy to Clipboard')
        export_plot_cb_button.clicked.connect(self.export_plot_2clipboard)
        toolsVBox.addWidget(export_plot_cb_button)        
        
        toolsVBox.addWidget(export_tos_img_group_box)
        ## 3.-2 Refreash Button
        refresh_button = QPushButton()
        refresh_button.setText('Refresh')
        refresh_button.clicked.connect(self.refresh)
        toolsVBox.addWidget(refresh_button)
        

        # Finish right panel
        toolsVBox.addStretch()
        baseHBox.addLayout(toolsVBox)

        self.setLayout(baseHBox)
        # self.setCentralWidget(self.widget)

    def segment_amount_LE_enter_predded(self):
        self.refresh()

    def subplot_button_toggled(self):
        self.plot()
    
    def export_plot_2clipboard(self):
        buf = io.BytesIO()
        self.sc.fig.savefig(buf, bbox_inches='tight')
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()

    def compute_strain_curves(self):
        N_sectors, N_frames = self.strain_matrix.shape
        N_segment = int(self.segment_amount_LE.text())
        segment_width = int(np.ceil(N_sectors / N_segment))
        self.strain_curves = []
        for strain_curve_idx in range(N_segment):
            segment_start_sector = strain_curve_idx * segment_width
            segment_end_sector = min((strain_curve_idx + 1) * segment_width, N_sectors)
            self.strain_curves.append(np.mean(self.strain_matrix[segment_start_sector:segment_end_sector], axis=0))            

    def plot(self, subplot=False, curve_names=None):
        if curve_names is None:
            if len(self.strain_curves) == 6:
                curve_names = [
                    'inferoseptal', 'inferior', 
                    'inferolateral', 'anterolateral', 
                    'anterior', 'anteroseptal']
            else:
                curve_names = [str(idx+1) for idx in range(len(self.strain_curves))]
        
        if len(self.strain_curves) <= 10:
            colors = ['tab:blue', 'tab:orange', 
                        'tab:green', 'tab:red', 
                        'tab:purple', 'tab:brown', 
                        'tab:pink', 'tab:gray', 
                        'tab:olive', 'tab:cyan']
        else:
            colors = [None] * len(self.strain_curves)

        # self.sc.axes.cla()  # Clear the canvas.
        self.sc.fig.clf()
        # print(self.radio_subplot.isChecked)
        linewidth = self.line_width_sbox.value()
        # ylim = [-0.2,0.2]
        ylim = [np.min(self.strain_matrix), np.max(self.strain_matrix)]
        if self.radio_subplot.isChecked():
            self.sc.axes = self.sc.fig.subplots(len(self.strain_curves), 1)
            for curve_idx in range(len(self.strain_curves)):
                self.sc.axes[curve_idx].plot(self.strain_curves[curve_idx], 
                    label=curve_names[curve_idx],
                    linewidth=linewidth,
                    color=colors[curve_idx])
                self.sc.axes[curve_idx].legend(loc='upper right')
                self.sc.axes[curve_idx].set_ylim(ylim)
        else:
            self.sc.axes = self.sc.fig.add_subplot(111)
            for curve_idx in range(len(self.strain_curves)):
                self.sc.axes.plot(self.strain_curves[curve_idx], 
                    label=curve_names[curve_idx],
                    linewidth=linewidth,
                    color=colors[curve_idx])
            self.sc.axes.legend(loc='upper right')
            self.sc.axes.set_ylim(ylim)
        # self.sc.fig.legend()
        self.sc.draw()
    
    def refresh(self, strain_matrix=None):
        if strain_matrix is not None and type(strain_matrix) is not bool:
            self.strain_matrix = strain_matrix
        self.compute_strain_curves()
        self.plot()