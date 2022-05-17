import os, sys, io
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore as Qt
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (QWidget, QPushButton, QButtonGroup, QFileDialog,
                             QHBoxLayout, QVBoxLayout, QApplication, QGroupBox, QRadioButton, 
                             QCheckBox, QLineEdit, QLabel)
from PyQt5.QtGui import QDrag, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar 
from matplotlib.figure import Figure


from scipy import interpolate
from scipy.interpolate import make_interp_spline
import scipy.io as sio

from components.draggables import DraggablePoint, DraggableLabel, XEllipse
from components.strain_matrix_canvas import MplCanvas
from components.strain_curves_viewer import StrainCurvesViewer

class ThreeDViewer(QtWidgets.QMainWindow):
    def createWindow(self, parent):
       super(ThreeDViewer,self).__init__(parent)

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.name = 'main_window'        
        self.data = {}
        self.adding_new_data = True # inside initialization process. Avoid refresh_plot too many times
        self.mat_loaded = False
        self.show_inversed_tos = False
        self.show_inversed_strainmat = False
        self.strainCurvesViewer = None
        self.linewidth = 3
        # self.setStyleSheet("background-color: white;")
        self.init_UI()
        #self.saveFileDialog()
        
        self.setAcceptDrops(True)
        self.setWindowTitle('Strain Matrix Viewer')
        # self.setDragEnabled(True)
        self.show()
        
    def init_UI(self):
        # print(getScreenSize())
        # screenHeight, screenWidth = getScreenSize()
        # self.setMaximumWidth(screenWidth//2)
        # self.setMaximumHeight(screenHeight//2)

        # 1. Base layout: hbox
        baseHBox = QHBoxLayout()
                
        # 2. Left panel: annotation canvas
        annoVBox = QVBoxLayout()
        
        self.sc = MplCanvas(self, width=10, height=4, dpi=100)
        # self.sc.axes.pcolor(np.zeros((32,32)), cmap='jet')
        self.sc.axes.text(0.5, 0.5, 'Drag & drop .mat file here to import', ha="center", va="center")
        # self.sc.axes.autoscale(False)
        self.sc.mpl_connect('button_press_event', self.clicked)
        toolbar = NavigationToolbar(self.sc, self)
        # self.setCentralWidget(toolbar)

        # layout = QtWidgets.QVBoxLayout()
        # layout.addWidget(toolbar)
        annoVBox.addWidget(self.sc)
        annoVBox.addWidget(toolbar)
        
        self.TOS_Label = QLabel()
        self.TOS_Label.setText('TOS(N): ')
        self.TOS_Label.setFixedHeight(20)
        self.TOS_Label.setAlignment(Qt.Qt.AlignCenter | Qt.Qt.AlignVCenter)
        annoVBox.addWidget(self.TOS_Label)
        
        self.TOS_loaded_Label = QLabel()
        self.TOS_loaded_Label.setText('TOS(L): ')
        self.TOS_loaded_Label.setFixedHeight(20)
        self.TOS_loaded_Label.setAlignment(Qt.Qt.AlignCenter | Qt.Qt.AlignVCenter)
        annoVBox.addWidget(self.TOS_loaded_Label)
        
        # baseHBox.addWidget(self.sc)
        baseHBox.addLayout(annoVBox)
        
        # 3. Right panel: settings and tools
        toolsVBox = QVBoxLayout() 
        # toolsVBoxWidth = 150
        toolsVBoxWidth = 250
        # toolsVBox.setFixedWidth(80)
        
        # 3.0 Resulution
        reso_group_box = QGroupBox("Segment Resolution")
        self.reso_btn_box = QButtonGroup()
        self.radio_18 = QRadioButton('18');      self.radio_18.clicked.connect(self.reso_button_toggled)
        self.radio_126 = QRadioButton('126');    self.radio_126.clicked.connect(self.reso_button_toggled)
        self.radio_18.setChecked(True);          self.seg_reso = 18
        self.radio_126.setEnabled(False)

        reso_group_box_layout = QVBoxLayout()
        reso_group_box_layout.addWidget(self.radio_18);self.reso_btn_box.addButton(self.radio_18, 0)
        reso_group_box_layout.addWidget(self.radio_126);self.reso_btn_box.addButton(self.radio_126, 1)
        reso_group_box.setLayout(reso_group_box_layout)
        reso_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(reso_group_box)

        # 3.1 Interpolation method
        interp_group_box = QGroupBox("Interpolation Method")
        self.interp_btn_box = QButtonGroup()
        radio_linear = QRadioButton('linear');  radio_linear.clicked.connect(self.interp_button_toggled)
        radio_spline = QRadioButton('spline');  radio_spline.clicked.connect(self.interp_button_toggled)
        radio_spline.setChecked(True); self.interp_k = 2
        
        interp_group_box_layout = QVBoxLayout()
        interp_group_box_layout.addWidget(radio_linear);self.interp_btn_box.addButton(radio_linear, 0)
        interp_group_box_layout.addWidget(radio_spline);self.interp_btn_box.addButton(radio_spline, 1)
        interp_group_box.setLayout(interp_group_box_layout)
        interp_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(interp_group_box)
        
        # 3.2 Visibility
        self.vis_strain_mat_checkBox = QCheckBox('Strain Matrix');    self.vis_strain_mat_checkBox.toggled.connect(self.vis_checkBox_toggled)
        self.vis_strain_mat_denoise_checkBox = QCheckBox('Denoise');   self.vis_strain_mat_denoise_checkBox.toggled.connect(self.vis_checkBox_toggled)
        self.vis_tos_new_checkBox    = QCheckBox('New TOS Curve');    self.vis_tos_new_checkBox.toggled.connect(self.vis_checkBox_toggled)
        self.vis_tos_loaded_checkBox = QCheckBox('Loaded TOS Curve'); self.vis_tos_loaded_checkBox.toggled.connect(self.vis_checkBox_toggled)
        self.vis_tos_Jerry_checkBox = QCheckBox('Loaded New TOS Curve (if exists)');   self.vis_tos_Jerry_checkBox.toggled.connect(self.vis_checkBox_toggled)
        self.vis_tos_otherRes_checkBox = QCheckBox('OtherRes TOS Curve'); self.vis_tos_otherRes_checkBox.toggled.connect(self.vis_checkBox_toggled)
        self.vis_strain_value_limit_checkBox = QCheckBox('Strain Value Limit'); self.vis_strain_value_limit_checkBox.toggled.connect(self.vis_strain_value_limit_checkBox_toggled)
        self.vis_strain_colorbar_checkBox = QCheckBox('Strain Colorbar');       self.vis_strain_colorbar_checkBox.toggled.connect(self.vis_strain_colorbar_checkBox_toggled)
        
        self.vis_strain_mat_checkBox.setEnabled(False)
        self.vis_strain_mat_denoise_checkBox.setEnabled(False)
        self.vis_tos_new_checkBox.setEnabled(False)
        self.vis_tos_loaded_checkBox.setEnabled(False)
        self.vis_tos_otherRes_checkBox.setEnabled(False)
        self.vis_strain_value_limit_checkBox.setEnabled(False)
        self.vis_strain_colorbar_checkBox.setEnabled(False)
        #self.vis_tos_loaded_ckeckBox.setChecked(True)
        vis_group_box = QGroupBox("Visibility")
        vis_group_box_layout = QVBoxLayout()
        vis_group_box_layout.addWidget(self.vis_strain_mat_checkBox)
        vis_group_box_layout.addWidget(self.vis_strain_mat_denoise_checkBox)
        vis_group_box_layout.addWidget(self.vis_tos_new_checkBox)
        vis_group_box_layout.addWidget(self.vis_tos_loaded_checkBox)
        vis_group_box_layout.addWidget(self.vis_tos_Jerry_checkBox)
        vis_group_box_layout.addWidget(self.vis_tos_otherRes_checkBox)
        vis_group_box_layout.addWidget(self.vis_strain_value_limit_checkBox)
        vis_group_box_layout.addWidget(self.vis_strain_colorbar_checkBox)
        vis_group_box.setLayout(vis_group_box_layout)
        vis_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(vis_group_box)

        # Other widgets
        others_group_box = QGroupBox("Others")
        others_group_layout = QVBoxLayout()
        # Show 3D plot
        self.view_3D_button = QPushButton('View 3D')
        self.view_3D_button.clicked.connect(self.view_3D_button_clicked)
        self.view_3D_button.setEnabled(False)
        others_group_layout.addWidget(self.view_3D_button)
        # Show Strain curves
        self.view_strain_curves_button = QPushButton('View Strain Curves')
        self.view_strain_curves_button.clicked.connect(self.view_strain_curves_button_clicked)
        self.view_strain_curves_button.setEnabled(False)
        others_group_layout.addWidget(self.view_strain_curves_button)        
        # Append all other widgets
        others_group_box.setLayout(others_group_layout)
        toolsVBox.addWidget(others_group_box)

        # 3.2-2 Annotator
        # Layout
        annotator_group_box = QGroupBox("Annotator")
        annotator_group_layout = QVBoxLayout()
        
        # Widgets
        self.annotator_LE = QLineEdit()
        # annotator_label = QLabel()
        # annotator_label.setText('Annotator')
        # annotator_group_layout.addWidget(annotator_label)
        annotator_group_layout.addWidget(self.annotator_LE)
        annotator_group_box.setLayout(annotator_group_layout)
        annotator_group_box.setFixedWidth(toolsVBoxWidth)
        toolsVBox.addWidget(annotator_group_box)

        # 3.3 Export
        # 3.3.1 Export .mat
        export_tos_mat_group_box = QGroupBox("Export Mat")
        export_tos_mat_group_layout = QVBoxLayout()
        
        # 3.3.1.1 Filename Area
        self.export_tos_mat_fname_LE = QLineEdit()
        export_tos_mat_ftype_label = QLabel()
        export_tos_mat_ftype_label.setText('.mat')
        export_tos_mat_filename_layout = QHBoxLayout()
        export_tos_mat_filename_layout.addWidget(self.export_tos_mat_fname_LE)
        export_tos_mat_filename_layout.addWidget(export_tos_mat_ftype_label)
        export_tos_mat_group_layout.addLayout(export_tos_mat_filename_layout)

        # 3.3.1.2 TOS-only Checkbox
        self.export_tos_mat_tos_only_checkBox = QCheckBox('TOS Only')
        self.export_tos_mat_tos_only_checkBox.toggled.connect(self.export_tos_only_checkBox_toggled)
        export_tos_mat_group_layout.addWidget(self.export_tos_mat_tos_only_checkBox)

        
        # 3.3.1.3 Drag Label
        export_tos_mat_label = DraggableLabel()
        export_tos_mat_label.setText('Drag Target Folder Here')
        export_tos_mat_label.setAlignment(Qt.Qt.AlignCenter | Qt.Qt.AlignVCenter)
        export_tos_mat_group_layout.addWidget(export_tos_mat_label)
        
        # 3.3.1.4 Export button
        export_tos_mat_button = QPushButton()
        export_tos_mat_button.setText('Export to File')
        export_tos_mat_button.clicked.connect(self.export_TOS_mat)
        export_tos_mat_group_layout.addWidget(export_tos_mat_button)
        
        export_tos_mat_group_box.setLayout(export_tos_mat_group_layout)
        export_tos_mat_group_box.setFixedWidth(toolsVBoxWidth)
        
        toolsVBox.addWidget(export_tos_mat_group_box)
        
        # 3.3.2 Export Image
        export_tos_img_group_box = QGroupBox("Export img")
        export_tos_img_group_layout = QVBoxLayout()
        
        # 3.3.2.1 Filename Area
        # self.app.matFilename
        self.export_tos_img_fname_LE = QLineEdit()
        export_tos_img_ftype_label = QLabel()
        export_tos_img_ftype_label.setText('.png')
        export_tos_img_filename_layout = QHBoxLayout()
        export_tos_img_filename_layout.addWidget(self.export_tos_img_fname_LE)
        export_tos_img_filename_layout.addWidget(export_tos_img_ftype_label)
        export_tos_img_group_layout.addLayout(export_tos_img_filename_layout)
        
        # 3.3.2.2 Drag Label
        export_tos_img_label = DraggableLabel()
        export_tos_img_label.setText('Drag Target Folder Here')
        export_tos_img_label.setAlignment(Qt.Qt.AlignCenter | Qt.Qt.AlignVCenter)
        export_tos_img_group_layout.addWidget(export_tos_img_label)
        
        # 3.3.2.3 Export to File button
        export_tos_img_button = QPushButton()
        export_tos_img_button.setText('Export to File')
        export_tos_img_button.clicked.connect(self.export_TOS_img)
        export_tos_img_group_layout.addWidget(export_tos_img_button)
        
        # 3.3.2.4 Export to Clipboard button
        export_tos_img_cb_button = QPushButton()
        export_tos_img_cb_button.setText('Copy to Clipboard')
        export_tos_img_cb_button.clicked.connect(self.export_TOS_img_2clipboard)
        export_tos_img_group_layout.addWidget(export_tos_img_cb_button)
        
        export_tos_img_group_box.setLayout(export_tos_img_group_layout)
        export_tos_img_group_box.setFixedWidth(toolsVBoxWidth)
        
        toolsVBox.addWidget(export_tos_img_group_box)
        
        # 4 Others
        others_group_box = QGroupBox("Others")
        others_group_layout = QVBoxLayout()
        
        # 4.1 Inverse TOS
        self.inverse_tos_checkBox = QCheckBox('Inverse TOS')
        self.inverse_tos_checkBox.toggled.connect(self.inverse_tos_toggled)
        others_group_layout.addWidget(self.inverse_tos_checkBox)

        # 4.2 Inverse strain matrix
        self.inverse_strainmat_checkBox = QCheckBox('Flip Strain Matrix')
        self.inverse_strainmat_checkBox.toggled.connect(self.inverse_strainmat_toggled)
        others_group_layout.addWidget(self.inverse_strainmat_checkBox)

        # 4.3 Copy TOS to clipboard
        # export_tos_18_cb_button = QPushButton()
        # export_tos_18_cb_button.setText('Copy to Clipboard')
        # export_tos_18_cb_button.clicked.connect(self.export_TOS_28_2_clipboard)
        # others_group_layout.addWidget(export_tos_18_cb_button)
        
        others_group_box.setLayout(others_group_layout)
        toolsVBox.addWidget(others_group_box)
        
        # 3.-1 Add Last strach
        toolsVBox.addStretch()
        
        baseHBox.addLayout(toolsVBox)
        
        self.widget = QWidget()
        self.widget.setLayout(baseHBox)
        self.setCentralWidget(self.widget)

    def reso_button_toggled(self):
        # print('T!')
        # print('id',self.interp_btn_box.checkedId())
        if self.reso_btn_box.checkedId() == 0:
            # if selected the low resolution option
            self.seg_reso = 18
            self.data_to_show = '18' if '18' in self.data.keys() else None
            
            # Subsample 126 -> 18
            tos_subsample = self.data['fullRes']['TOS_new'][::7]# + 7//2
            self.data[self.data_to_show]['tos_from_other_reso'] = tos_subsample

        elif self.reso_btn_box.checkedId() == 1:
            # if selected the high resolution option
            self.seg_reso = 126
            self.data_to_show = 'fullRes' if 'fullRes' in self.data.keys() else None            

            # Interpolate 18 -> 126
            xs_18  = np.linspace(1, 17, 18)
            xs_126 = np.linspace(1, 17, 126)
            # tos_interp = np.interp(xs_126, xs_18,self.data['18']['TOS'])
            f_interp = interpolate.interp1d(xs_18,self.data['18']['TOS_new'], kind = 'quadratic')
            self.data[self.data_to_show]['tos_from_other_reso'] = np.maximum(f_interp(xs_126), 17)
        self.init_tos_line()
        if self.mat_loaded and not self.adding_new_data:
            self.refresh_plot()

    def interp_button_toggled(self):
        # print('T!')
        # print('id',self.interp_btn_box.checkedId())
        if self.interp_btn_box.checkedId() == 0:
            self.interp_k = 1
        elif self.interp_btn_box.checkedId() == 1:
            self.interp_k = 2
        if self.mat_loaded and not self.adding_new_data:
            self.refresh_plot()
    
    def vis_checkBox_toggled(self):
        self.vis_strain_mat = self.vis_strain_mat_checkBox.isChecked()
        self.vis_tos_loaded = self.vis_tos_loaded_checkBox.isChecked()
        self.vis_tos_new    = self.vis_tos_new_checkBox.isChecked()
        self.vis_tos_Jerry  = self.vis_tos_Jerry_checkBox.isChecked()
        self.vis_tos_otherRes = self.vis_tos_otherRes_checkBox.isChecked()
        if not self.adding_new_data:
            self.refresh_plot()
    
    def vis_strain_value_limit_checkBox_toggled(self):
        if not self.adding_new_data:
            # if self.vis_strain_colorbar_checkBox.isChecked():
            #     self.matplot_colobar.update_normal(mappable=self.matplot)
                # self.matplot_colobar.update_bruteforce(mappable=self.matplot)
            self.refresh_plot()
        # if self.vis_strain_value_limit_checkBox.isChecked():
        #     self.
    
    def vis_strain_colorbar_checkBox_toggled(self):
        # https://stackoverflow.com/questions/5263034/remove-colorbar-from-figure-in-matplotlib
        if not self.adding_new_data:
            if self.vis_strain_colorbar_checkBox.isChecked():
                self.matplot_colobar = self.sc.fig.colorbar(self.matplot, ax=self.sc.fig.axes)
            else:
                self.sc.fig.delaxes(self.sc.fig.axes[1])
                self.sc.fig.subplots_adjust(right=0.90)
                # self.matplot_colobar.remove()
            self.refresh_plot()
    
    def view_3D_button_clicked(self):
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib import cm
        # self.window_to_open = ThreeDViewer(self)
        # self.window_to_open.show()
        # print("HH")
        # fig, axe = plt.subplots()
        # xs = np.random.rand(10)
        # axe.plot(xs)
        # H, W = self.data[self.data_to_show]['mat'].shape
        # fig.show()

        # Get strain matrix
        mat = self.data[self.data_to_show]['mat']
        
        # Create figure and 3D axis
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Draw 3D GT Line
        # self.data[data_name]['tos_curve_sectors'] = np.arange(0.5, self.data[data_name]['NSegments']-0.5, 0.1)
        # self.data[data_name]['tos_curve_frames'] = [0.5]*len(self.data[data_name]['tos_curve_sectors'])
        # tos_GT_ys = np.arange(self.data[self.data_to_show]['tos_curve_sectors'])
        # tos_GT_xs = np.arange(self.data[self.data_to_show]['tos_curve_frames'])
        # tos_GT_zs = np.zeros(len(tos_GT_xs))
        # for idx in range(len(tos_GT_xs)):
        #     tos_GT_zs[idx] = 0

        if self.vis_strain_value_limit_checkBox.isChecked():
            vmax = 0.2
            vmin = -0.2
        else:
            vmax = None
            vmin = None

        mat_xs, mat_ys = np.meshgrid(np.arange(mat.shape[1]), np.arange(mat.shape[0]))
        ax.plot_surface(mat_xs, mat_ys, mat, cmap='jet',
                        vmax = vmax, vmin = vmin, 
                       antialiased=False, linewidth=0.2, edgecolor="dodgerblue")
        # ax.plot_wireframe(mat_xs, mat_ys, mat, linewidth = 0.5)

        fig.show()

    def view_strain_curves_button_clicked(self):
        self.strainCurvesViewer = StrainCurvesViewer(self.strainmat_to_show)
        self.strainCurvesViewer.show()

    def inverse_tos_toggled(self):
        self.show_inversed_tos = not self.show_inversed_tos
        # if self.TOS is not None:
        #     self.TOS = self.TOS[::-1]
        # if self.tos_loaded is not None:
        #     self.tos_loaded = self.tos_loaded[::-1]
        # for data_name in self.data.keys():
        #     print(data_name, self.data[data_name].keys())
        #     # try:
        #     self.data[data_name]['TOS'] = self.data[data_name]['TOS'][::-1]
        #     self.data[data_name]['TOSNew'] = self.data[data_name]['TOSNew'][::-1]
            # except:
            #     pass
        if not self.adding_new_data:
            self.refresh_plot()
    
    def inverse_strainmat_toggled(self):
        self.show_inversed_strainmat = not self.show_inversed_strainmat
        if not self.adding_new_data:
            self.refresh_plot()
    
    
    def export_tos_only_checkBox_toggled(self):
        save_filename_main = self.export_tos_mat_fname_LE.text().replace('_tos', '')
        if self.export_tos_mat_tos_only_checkBox.isChecked():
            self.export_tos_mat_fname_LE.setText(save_filename_main + '_tos')
            # self.export_tos_only = True
        else:
            self.export_tos_mat_fname_LE.setText(save_filename_main)
            # self.export_tos_only = False

    def clicked(self, event):
        if event.button==2:
            # middle click to add control point
            # print('clicked!', event.xdata, event.ydata)
            xdata = max(event.xdata, 0.5)
            ydata = event.ydata
            self.ctl_points_to_show.append(
                XEllipse((xdata,ydata),  self.ctl_point_to_show_w, self.ctl_point_to_show_h, fc='r', alpha=0.5)
                )
            self.data[self.data_to_show]['ctl_points'].append(self.ctl_points_to_show[-1])
            self.update_plot()    
    
    def draw_ctl_points(self, ):        
        self.drs = []
        for circ in self.ctl_points_to_show:
            circ.width, circ.height = self.ctl_point_to_show_w, self.ctl_point_to_show_h
            self.sc.axes.add_patch(circ)
            dr = DraggablePoint(circ, self)
            dr.connect()
            self.drs.append(dr)
        self.sc.draw()
    
    def interp_given_ctrl_points(self):
        if len(self.ctl_points_to_show) < 3:
            return
        ctl_point_frames_plot, ctl_point_sectors_plot = zip(*[circ.get_center() for circ in self.ctl_points_to_show])
        order = np.argsort(ctl_point_sectors_plot)
        # print(order)
        ctl_point_frames_plot = [ctl_point_frames_plot[idx] for idx in order]
        ctl_point_sectors_plot = [ctl_point_sectors_plot[idx] for idx in order]        
        
        # print('INTERP!')
        # f = interpolate.interp1d(ctl_point_sectors, ctl_point_frames, fill_value="extrapolate", kind = self.interpolate_method)
        f = make_interp_spline(ctl_point_sectors_plot, ctl_point_frames_plot, k=self.interp_k)
        
        # self.tos_curve_sectors = np.arange(0.5, self.data[self.data_to_show]['NSegments']-0.5, 0.1)
        # self.tos_curve_frames  = f(self.tos_curve_sectors)
        # self.tos_curve_frames[self.tos_curve_frames<0.5] = 0.5
        # print(self.data.keys())
        # print(self.data_to_show)
        self.data[self.data_to_show]['tos_curve_sectors'] = np.arange(0.5, self.data[self.data_to_show]['NSegments']-0.5, 0.1)
        self.data[self.data_to_show]['tos_curve_frames']  = np.maximum(f(self.data[self.data_to_show]['tos_curve_sectors']), 0.5)
            
        # point at (0.5, 0.5)  should have sector 0, frame 0, time 17
        # self.TOS = (f(np.arange(self.data[self.data_to_show]['NSegments'])+0.5) + 0.5) * 17
        # self.TOS[self.TOS < 17] = 17
        self.data[self.data_to_show]['TOS_new'] = np.maximum((f(np.arange(self.data[self.data_to_show]['NSegments'])+0.5) + 0.5) * 17, 17)
        # self.TOS[self.TOS < 17] = 17
        
        # self.TOS = self.TOS[::-1]
        TOSStr = ' '.join([f'{tos:.2f} ' for tos in self.data[self.data_to_show]['TOS_new']])
        # self.TOS_Label.setText('TOS(N): ' + TOSStr)
        
        #TOSStr = ' '.join([f'{tos:.2f} ' for tos in self.TOS[::-1]])
        #self.TOS_Label.setText('TOS (reversed): ' + TOSStr)
        
    def init_ctrl_points(self, event = None):
        # initialize control points
        scW, scH = self.sc.fig.get_size_inches()
        for data_name in self.data.keys():
            # self.ctl_point_to_show_w, self.ctl_point_to_show_h = 4/scH, 4/scW
            ctl_point_w, ctl_point_h = \
                4/scW, (self.data[data_name]['NSegments'] / 18)*(2/scH)
            self.data[data_name]['ctl_point_w'], self.data[data_name]['ctl_point_h'] = \
                ctl_point_w, ctl_point_h
            self.data[data_name]['ctl_points'] = [
                XEllipse((0.5,0.5),  ctl_point_w, ctl_point_h, fc='r', alpha=0.5),
                XEllipse((0.5,self.data[data_name]['NSegments']/2),  ctl_point_w, ctl_point_h, fc='r', alpha=0.5),
                XEllipse((0.5,self.data[data_name]['NSegments'] - 0.5),  ctl_point_w, ctl_point_h, fc='r', alpha=0.5)
                ]
        # self.interp_given_ctrl_points()
            self.data[data_name]['tos_curve_sectors'] = np.arange(0.5, self.data[data_name]['NSegments']-0.5, 0.1)
            self.data[data_name]['tos_curve_frames'] = [0.5]*len(self.data[data_name]['tos_curve_sectors'])
        # tos_curve_sectors_init = np.arange(0.5, self.data[self.data_to_show]['NSegments']-0.5, 0.1)
        # tos_curve_frames_init = [0.5]*len(tos_curve_sectors_init)
        # # print(tos_curve_sectors_init, tos_curve_frames_init)
        
        # self.tos_curve_line, = self.sc.axes.plot(tos_curve_frames_init, tos_curve_sectors_init)
        # self.tos_curve_line.set_label('New')
        
        # self.sc.axes.add_artist(self.tos_curve_line)

    # def init_plot_old(self, event = None):
    #     # initialize control points
    #     scW, scH = self.sc.fig.get_size_inches()
    #     self.ctl_point_to_show_w, self.ctl_point_to_show_h = 4/scH, 4/scW
    #     # self.ctl_point_to_show_w, self.ctl_point_to_show_h = 4/scW, (self.data[self.data_to_show]['NSegments'] / 18)*(2/scH)
    #     self.ctl_points = [
    #         XEllipse((0.5,0.5),  self.ctl_point_to_show_w, self.ctl_point_to_show_h, fc='r', alpha=0.5),
    #         XEllipse((0.5,self.data[self.data_to_show]['NSegments']/2),  self.ctl_point_to_show_w, self.ctl_point_to_show_h, fc='r', alpha=0.5),
    #         XEllipse((0.5,self.data[self.data_to_show]['NSegments'] - 0.5),  self.ctl_point_to_show_w, self.ctl_point_to_show_h, fc='r', alpha=0.5)
    #         ]
    #     # self.interp_given_ctrl_points()
    #     tos_curve_sectors_init = np.arange(0.5, self.data[self.data_to_show]['NSegments']-0.5, 0.1)
    #     tos_curve_frames_init = [0.5]*len(tos_curve_sectors_init)
    #     # print(tos_curve_sectors_init, tos_curve_frames_init)
        
    #     self.tos_curve_line, = self.sc.axes.plot(tos_curve_frames_init, tos_curve_sectors_init)
    #     self.tos_curve_line.set_label('New')
        
    #     self.sc.axes.add_artist(self.tos_curve_line)
        
    def init_tos_line(self):
        # print('init line!')
        # print(self.data_to_show)
        # print(len(self.data[self.data_to_show]['tos_curve_frames']))
        # print(len(self.data[self.data_to_show]['tos_curve_sectors']))
        self.tos_curve_line, = self.sc.axes.plot(self.data[self.data_to_show]['tos_curve_frames'], self.data[self.data_to_show]['tos_curve_sectors'], linewidth=self.linewidth)
        self.tos_curve_line.set_label('New')

    def update_tos_line(self, interpolate = True):
        # Draw tos curve using updated control points
        # print('update_tos_line')
        if interpolate:
            self.interp_given_ctrl_points()
        
        tos_curve_frames_toshow = self.data[self.data_to_show]['tos_curve_frames']
        if self.show_inversed_tos:
            tos_curve_frames_toshow = tos_curve_frames_toshow[::-1]
        self.tos_curve_line.set_xdata(tos_curve_frames_toshow)
        self.tos_curve_line.set_color('r')
    
    def update_plot(self, event = None):
        # Update only ctl points and tos curve
        # print('update_plot')
        # print(event)
        self.ctl_points_to_show = [ctl_point for ctl_point in self.data[self.data_to_show]['ctl_points'] if ctl_point.deactivated == False]
        scW, scH = self.sc.fig.get_size_inches()
        # print(scW, scH)
        # self.ctl_point_to_show_w, self.ctl_point_to_show_h = 4/scW, 2/scH
        # self.ctl_point_to_show_w, self.ctl_point_to_show_h = 1, 1
        self.ctl_point_to_show_w, self.ctl_point_to_show_h = 4/scW, (self.data[self.data_to_show]['NSegments'] / 18)*(2/scH)
        self.update_tos_line()
        self.tos_curve_line.set_color('orange')
        self.draw_ctl_points()
    
    def refresh_plot(self):
        # Redraw the whole canvas        
        
        # Clean
        self.sc.axes.cla()  # Clear the canvas.
        
        # Set Title
        n_words = len(self.matFilenameFull.split('/'))
        title = '/'.join(self.matFilenameFull.split('/')[:int(n_words/2)]) + '\n' \
            + '/'.join(self.matFilenameFull.split('/')[int(n_words/2):])
        self.sc.axes.set_title(title, fontsize = 10)
        
        # Set limit and tick
        self.sc.axes.set_xlim(0, self.data[self.data_to_show]['NFrames'])
        self.sc.axes.set_ylim(0, self.data[self.data_to_show]['NSegments'])
        # self.sc.axes.set_xticks(np.arange(self.data_to_show['NFrames'])+0.5)
        # self.sc.axes.set_xticklabels(np.arange(self.data_to_show['NFrames']))
        # self.sc.axes.set_yticks(np.arange(self.data_to_show['NSegments'])+0.5)
        # self.sc.axes.set_yticklabels(np.arange(self.data_to_show['NSegments'])+1)        
        # self.sc.axes.autoscale(False)

        # Re-draw strain matrix
        if self.vis_strain_mat_checkBox.isChecked():
            if self.vis_strain_value_limit_checkBox.isChecked():
                vmax = 0.2
                vmin = -0.2
            else:
                vmax = None
                vmin = None
            if self.vis_strain_mat_denoise_checkBox.isChecked():
                self.strain_mat_type = 'mat_denoised'
            else:
                self.strain_mat_type = 'mat'
            if self.data[self.data_to_show][self.strain_mat_type] is not None:
                self.strainmat_to_show = self.data[self.data_to_show][self.strain_mat_type]
                # self.matplot = self.sc.axes.pcolor(self.data[self.data_to_show][strain_mat_type], cmap='jet', vmax = vmax, vmin = vmin)
                
            else:
                self.strainmat_to_show = self.data['18'][self.strain_mat_type]
                # self.matplot = self.sc.axes.pcolor(self.data['18'][strain_mat_type], cmap='jet', vmax = vmax, vmin = vmin)                
                # raise ValueError('NO MAT')
            if self.inverse_strainmat_checkBox.isChecked():
                self.strainmat_to_show = np.flip(self.strainmat_to_show, axis=0)

            self.matplot = self.sc.axes.pcolor(self.strainmat_to_show, cmap='jet', vmax = vmax, vmin = vmin)

            if self.vis_strain_colorbar_checkBox.isChecked():
                self.matplot_colobar.update_normal(mappable=self.matplot)
            # elif self.seg_reso == 126 and self.matFullRes is not None:
            #     self.sc.axes.pcolor(self.matFullRes, cmap='jet', vmax = 0.2, vmin = -0.2)
            # if self.vis_strain_colorbar_checkBox.isChecked():
            #     self.matplot_colobar = self.sc.fig.colorbar(self.matplot, ax=self.sc.fig.axes)
            # else:
            #     self.matplot_colobar.remove()
        # print(self.data_to_show['mat'].shape)
        # self.sc.axes.set_size_inches(5,1)
        # self.sc.fig.set_size_inches(5,1)
        # https://stackoverflow.com/questions/14754931/matplotlib-values-under-cursor
        numrows, numcols = self.data[self.data_to_show]['mat'].shape
        def format_coord(x, y):
            col = int(x+0.5)
            row = int(y+0.5)
            if col>=0 and col<numcols and row>=0 and row<numrows:
                z = self.data[self.data_to_show]['mat'][row,col]
                return 'x=%1.4f, y=%1.4f, z=%1.4f'%(x, y, z)
            else:
                return 'x=%1.4f, y=%1.4f'%(x, y)

        self.sc.axes.format_coord = format_coord



        # # Re-draw control points and tos curve
        lines_to_show = []
        # line_colors = ['black']
        if self.vis_tos_new_checkBox.isChecked():
            self.update_plot()
            lines_to_show.append({'line': self.tos_curve_line, 'legend': 'new'})
            # self.sc.axes.add_artist(self.tos_curve_line)
            # self.tos_curve_line.set_label('New')
            # self.sc.axes.legend([self.tos_curve_line], ['new'])
        
        # print(self.data_to_show['TOS'].shape)
        if self.data[self.data_to_show]['TOS_loaded'] is not None and self.vis_tos_loaded_checkBox.isChecked():
            tos_loaded_toshow = self.data[self.data_to_show]['TOS_loaded'][::-1] if self.show_inversed_tos else self.data[self.data_to_show]['TOS_loaded']
            self.tos_loaded_line, = self.sc.axes.plot(tos_loaded_toshow / 17 - 0.5 , np.arange(len(self.data[self.data_to_show]['TOS_loaded']))+0.5, color='black', linewidth=self.linewidth)
            lines_to_show.append({'line':self.tos_loaded_line, 'legend':'loaded GT'})

        if self.data[self.data_to_show]['TOS_loaded_new'] is not None and self.vis_tos_Jerry_checkBox.isChecked():
            tos_Jerry_toshow  = self.data[self.data_to_show]['TOS_loaded_new'][::-1] if self.show_inversed_tos else self.data[self.data_to_show]['TOS_loaded_new']
            self.tos_Jerry_line,  = self.sc.axes.plot(tos_Jerry_toshow / 17 - 0.5 , np.arange(len(self.data[self.data_to_show]['TOS_loaded_new']))+0.5, color='blue', linewidth=self.linewidth)
            lines_to_show.append({'line':self.tos_Jerry_line, 'legend':'Loaded New'})

        if self.vis_tos_otherRes_checkBox.isChecked() and 'tos_from_other_reso' in self.data[self.data_to_show].keys():
            tos_otherRes_toshow = self.data[self.data_to_show]['tos_from_other_reso'][::-1] if self.show_inversed_tos else self.data[self.data_to_show]['tos_from_other_reso']
            self.tos_otherRes_line, = self.sc.axes.plot(tos_otherRes_toshow / 17 - 0.5 , np.arange(len(self.data[self.data_to_show]['tos_from_other_reso']))+0.5, color='green', linewidth=self.linewidth)
            lines_to_show.append({'line':self.tos_otherRes_line, 'legend':'otherRes'})
        
        for line in lines_to_show:
            self.sc.axes.add_artist(line['line'])
        self.sc.axes.legend([line['line'] for line in lines_to_show], [line['legend'] for line in lines_to_show])
        # TOS_linewidth = 7
        # Show loaded TOS
        """
        if self.data[self.data_to_show]['TOS'] is not None and self.vis_tos_loaded_checkBox.isChecked():
            tos_loaded_toshow = self.data[self.data_to_show]['TOS'][::-1] if self.show_inversed_tos else self.data[self.data_to_show]['TOS']
            tos_Jerry_toshow  = self.data[self.data_to_show]['TOS_Jerry'][::-1] if self.show_inversed_tos else self.data[self.data_to_show]['TOS_Jerry']
            self.tos_loaded_line, = self.sc.axes.plot(tos_loaded_toshow / 17 - 0.5 , np.arange(len(self.data[self.data_to_show]['TOS']))+0.5)
            self.tos_Jerry_line,  = self.sc.axes.plot(tos_Jerry_toshow / 17 - 0.5 , np.arange(len(self.data[self.data_to_show]['TOS_Jerry']))+0.5)
            # print(len(tos_loaded_toshow / 17 - 0.5), len(np.arange(len(self.data_to_show['TOS']))+0.5))
            # print(self.sc.axes)
            self.sc.axes.add_artist(self.tos_loaded_line)
            self.sc.axes.legend([self.tos_curve_line, self.tos_loaded_line, self.tos_Jerry_line], ['new', 'loaded', 'Jerry'])
            # self.TOS_loaded_Label.setText('TOS(L): ' + ' '.join([f'{tos:.2f} ' for tos in self.data_to_show['TOS']]))
            # self.tos_loaded_line.set_label('Loaded')
        #self.sc.axes.legend()

        # Show TOS interpolated / subsampled from the other resolution
        
        if self.vis_tos_otherRes_checkBox.isChecked() and 'tos_from_other_reso' in self.data[self.data_to_show].keys():
            tos_otherRes_toshow = self.data[self.data_to_show]['tos_from_other_reso'][::-1] if self.show_inversed_tos else self.data[self.data_to_show]['tos_from_other_reso']
            self.tos_otherRes_line, = self.sc.axes.plot(tos_otherRes_toshow / 17 - 0.5 , np.arange(len(self.data[self.data_to_show]['tos_from_other_reso']))+0.5, color='green')
            self.sc.axes.add_artist(self.tos_otherRes_line)
            if self.data[self.data_to_show]['TOS'] is not None:
                self.sc.axes.legend([self.tos_curve_line, self.tos_loaded_line, self.tos_otherRes_line], ['new', 'loaded', 'otherRes'])
            else:
                self.sc.axes.legend([self.tos_curve_line, self.tos_otherRes_line], ['new', 'otherRes'])
        """
        self.sc.draw()

        # Also refresh the 
        if self.strainCurvesViewer is not None and self.strainCurvesViewer.isVisible():
            self.strainCurvesViewer.refresh(self.strainmat_to_show)
    
    
    def saveFileDialog(self, fileType, directory):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        export_fileName, _ = QFileDialog.getSaveFileName(parent = self,
                                                         caption = "Save as",
                                                         directory = directory,
                                                         filter = f"{fileType};;All Files (*)", options=options)        
        if export_fileName:
            self.export_fileName = export_fileName
        else:
            self.export_fileName = None
    
    def export_TOS_mat(self):
        self.saveFileDialog('Matlab File (*.mat)', self.matDirectory + self.export_tos_mat_fname_LE.text() + '.mat')
        if self.export_fileName:
            # annotator_str = '_' + self.annotator_LE.text() if len(self.annotator_LE.text())>0 else ''
            annotator_str = self.annotator_LE.text() if len(self.annotator_LE.text())>0 else ''
            if not self.export_fileName.endswith('.mat'):
                self.export_fileName += '.mat'
            if self.export_tos_mat_tos_only_checkBox.isChecked():
                # If only export tos curves
                tos_data = {'annotator': annotator_str}
                if self.data['18']['TOS_loaded'] is not None:
                    tos_data['xs'] = self.data['18']['TOS_loaded']
                else:
                    tos_data['xs'] = np.zeros(len(self.data['18']['TOS_new']))
                
                if self.data['fullRes']['TOS_loaded'] is not None:
                    tos_data['xsfullRes'] = self.data['fullRes']['TOS_loaded']
                else:
                    tos_data['xsfullRes'] = np.zeros(len(self.data['fullRes']['TOS_new']))

                for data_name in self.data.keys():
                    # tos_data['TOS' + data_name + annotator_str] = np.flip(self.data[data_name]['TOSNew'])
                    # tos_data['xs' + data_name + '_new'] = np.flip(self.data[data_name]['TOS_new'])
                    tos_data['xs' + data_name + '_new'] = self.data[data_name]['TOS_new']
                sio.savemat(self.export_fileName, tos_data)
            else:
                # ELse if export all data
                if 'TOSAnalysis' not in self.dataRaw.keys():
                    no_tosanalysis = True
                    self.dataRaw['TOSAnalysis'] = {}
                else:
                    no_tosanalysis = False
                for data_name in self.data.keys():
                    if no_tosanalysis:
                        # exec("self.dataRaw['TOSAnalysis'].TOS" + data_name + annotator_str +  "=self.data[data_name]['TOSNew']")
                        # print(self.data[data_name]['TOSNew'].shape)
                        # self.dataRaw['TOSAnalysis']['TOS' + data_name + annotator_str] = np.flip(self.data[data_name]['TOSNew'])
                        # self.dataRaw['TOSAnalysis']['xs' + data_name + '_new'] = np.flip(self.data[data_name]['TOS_new'])
                        self.dataRaw['TOSAnalysis']['xs' + data_name + '_new'] = self.data[data_name]['TOS_new']
                    else:
                        # exec("self.dataRaw['TOSAnalysis'].TOS" + data_name + annotator_str +  "=np.flip(self.data[data_name]['TOSNew'])")                
                        exec("self.dataRaw['TOSAnalysis'].TOS" + data_name + annotator_str +  "=self.data[data_name]['TOSNew']")

                # Remove functions in SequenceInfo
                seq_rows, seq_cols = self.dataRaw['SequenceInfo'].shape
                for seq_row_idx in range(seq_rows):
                    for seq_col_idx in range(seq_cols):
                        self.dataRaw['SequenceInfo'][seq_row_idx][seq_col_idx].tform = ''
                
                # Save full resolution strain matrix if needed
                if self.data['fullRes']['save']:
                    self.dataRaw['StrainInfo'].CCmid = self.data['fullRes']['mat']
                    # exec("self.dataRaw['TOSAnalysis'].TOS" + data_name + annotator_str +  "=np.flip(self.data[data_name]['TOSNew'])")

                sio.savemat(self.export_fileName, self.dataRaw, long_field_names = True)
    
    def export_TOS_img(self):
        self.saveFileDialog('PNG Files (*.png)', self.matDirectory + self.export_tos_img_fname_LE.text() + '.png')
        if self.export_fileName:
            if not self.export_fileName.endswith('.png'):
                self.export_fileName += '.png'
            
            self.sc.fig.savefig(self.export_fileName, bbox_inches='tight')
            
    def export_TOS_img_2clipboard(self):
        # https://stackoverflow.com/questions/31607458/how-to-add-clipboard-support-to-matplotlib-figures
        buf = io.BytesIO()
        self.sc.fig.savefig(buf, bbox_inches='tight')
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()


        # self.saveFileDialog('PNG Files (*.png)', self.matDirectory + self.export_tos_img_fname_LE.text() + '.png')
        # if self.export_fileName:
        #     if not self.export_fileName.endswith('.png'):
        #         self.export_fileName += '.png'
            
        #     self.sc.fig.savefig(self.export_fileName, bbox_inches='tight')
    # def export_TOS_18_2_clipboard(self):
    #     # https://stackoverflow.com/questions/31607458/how-to-add-clipboard-support-to-matplotlib-figures
    #     buf = io.BytesIO()
    #     self.sc.fig.savefig(buf, bbox_inches='tight')
    #     QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
    #     buf.close()
    