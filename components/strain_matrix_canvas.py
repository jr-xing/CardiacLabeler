from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar 
from matplotlib.figure import Figure
from utils import loadStrainMat, saveTOS2Mat, getScreenSize, SVDDenoise, getStrainMatFull
from scipy import interpolate
from scipy.interpolate import make_interp_spline
import os, sys, io
import scipy.io as sio
import numpy as np

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)        
        self.app = parent
        self.app.tos_loaded = None
        # self.fig.tight_layout()
        
        super(MplCanvas, self).__init__(self.fig)
        self.setAcceptDrops(True)
        
    
    def dragEnterEvent(self, event):
        # print('dragged in')
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        print(event)
        # print('drag out')
            
    def dropEvent(self, event):
        # print('DROP!')
        self.app.adding_new_data = True
        files = [str(u.toLocalFile()) for u in event.mimeData().urls()]
        if '.mat' in files[0]:
            # print('MAT!')
            # print(self.app.name)
            self.app.matFilenameFull = files[0]
            # self.app.matFilename = self.app.matFilenameFull.split('/')[-1]
            
            # mat, tos, matFullRes, tosFullRes, dataRaw = loadStrainMat(files[0])
            dataDict = loadStrainMat(files[0])
            mat = dataDict['strainMat']
            if mat is not None:
                mat_denoised = SVDDenoise(mat)
            else:
                mat_denoised = None
            # tos = dataDict['TOS']
            matFullRes = dataDict['strainMatFullResolution']
            # tosFullRes = dataDict['TOSInterpolatedMid']
            dataRaw = dataDict['datamat']
            
            # flipStrainMat = True
            self.app.dataRaw = dataRaw
            if mat is None and matFullRes is None:
                matFullRes = None
                matFullRes_denoised = None
            elif mat is not None and matFullRes is None:
                # If get lower dimensional strain matrix but no full resolution
                # matFullRes = np.flipud(getStrainMatFull(sio.loadmat(files[0], struct_as_record=False, squeeze_me = True)))
                # matFullRes = np.flipud(SVDDenoise(getStrainMatFull(sio.loadmat(files[0], struct_as_record=False, squeeze_me = True))))
                matFullRes = getStrainMatFull(sio.loadmat(files[0], struct_as_record=False, squeeze_me = True))
                matFullRes_denoised = SVDDenoise(matFullRes)
                SaveMatFullRes = True
            else:
                SaveMatFullRes = False
                matFullRes_denoised = SVDDenoise(matFullRes)

            # print(tosFullRes == None)
            if mat is not None:
                # print('STRAINMAT!')
                self.app.data = {
                    '18': {
                        'mat': mat,
                        'mat_denoised': mat_denoised,
                        'TOS_loaded': dataDict['TOS'],
                        'TOS_new': np.zeros(18),
                        'TOS_loaded_new': dataDict['TOS18_new'],
                        'NSegments': mat.shape[0],
                        'NFrames': mat.shape[1],
                        'save': False
                    },
                    'fullRes': {
                        'mat': matFullRes,
                        'mat_denoised': matFullRes_denoised,
                        'TOS_loaded': dataDict['TOSInterpolatedMid'],
                        'TOS_new': np.zeros(126),
                        'TOS_loaded_new': dataDict['TOS126_new'],
                        'NSegments': matFullRes.shape[0] if matFullRes is not None else None,
                        'NFrames': matFullRes.shape[1] if matFullRes is not None else None,
                        'save': SaveMatFullRes
                    }
                }
                if matFullRes is not None:
                    self.app.radio_126.setEnabled(True)
                # else:
                #     matFullRes = getStrainMatFull
                if self.app.reso_btn_box.checkedId() == 0:
                    # self.app.data_to_show = self.app.data['18']
                    self.app.data_to_show = '18'
                    # self.app.tos_loaded = self.app.data['18']['TOS']
                elif self.app.reso_btn_box.checkedId() == 1:
                    self.app.data_to_show = 'fullRes'
                    # self.app.data_to_show = self.app.data['fullRes']
                    # self.app.tos_loaded = self.app.data['fullRes']['TOS']
                else:
                    raise ValueError('DATATOSHOW')

                self.app.matFilename = os.path.basename(self.app.matFilenameFull)
                self.app.matDirectory = os.path.dirname(self.app.matFilenameFull) + '/'
                self.app.sc.mpl_connect('resize_event', self.app.update_plot)
                
                # self.app.NSectors, self.app.NFrames = mat.shape
                # self.app.mat = mat
                self.app.mat_loaded = True
                # self.app.NSectorsFullRes = matFullRes.shape[0] if matFullRes is not None else 0
                # self.app.matFullRes = matFullRes
                
                # self.app.export_tos_mat_fname_LE.setText(self.app.matFilename.split('.')[0])
                # self.app.export_tos_img_fname_LE.setText(self.app.matFilename.split('.')[0])
                if self.app.export_tos_mat_tos_only_checkBox.isChecked():
                    self.app.export_tos_mat_fname_LE.setText('.'.join(self.app.matFilename.split('.')[:-1])+'_tos')
                else:
                    self.app.export_tos_mat_fname_LE.setText('.'.join(self.app.matFilename.split('.')[:-1]))
                self.app.export_tos_img_fname_LE.setText('.'.join(self.app.matFilename.split('.')[:-1]))
                # self.app.tos_loaded = None
                # self.app.init_plot()
                
                self.app.vis_strain_mat_checkBox.setEnabled(True)
                self.app.vis_strain_mat_checkBox.setChecked(True)
                self.app.vis_strain_mat_denoise_checkBox.setEnabled(True)
                self.app.vis_tos_new_checkBox.setEnabled(True)
                self.app.vis_tos_new_checkBox.setChecked(True)
                self.app.vis_tos_otherRes_checkBox.setEnabled(True)
                self.app.vis_strain_value_limit_checkBox.setEnabled(True)
                self.app.vis_strain_value_limit_checkBox.setChecked(True)
                self.app.vis_strain_colorbar_checkBox.setEnabled(True)
                self.app.vis_strain_colorbar_checkBox.setChecked(False)
                self.app.view_3D_button.setEnabled(True)
                self.app.view_strain_curves_button.setEnabled(True)            
            
            # print('DATATOSHOW!')
            
            # print(self.data_to_show)
        else:
            print(f'dont accept {files[0].split(".")[-1]} files')
            # self.app.tos_loaded = tos
        if dataDict['TOS'] is not None:
            self.app.vis_tos_loaded = True
            self.app.vis_tos_loaded_checkBox.setEnabled(True)
            # self.app.vis_tos_loaded_checkBox.setChecked(True)
            if len(dataDict['TOS']) == 18:
                self.app.data['18']['TOS_loaded'] = dataDict['TOS']
            else:
                self.app.data['fullRes']['TOS_loaded'] = dataDict['TOS']
            self.app.data['18']['TOS_loaded_new'] = dataDict['TOS18_new']
            self.app.data['fullRes']['TOS_loaded_new'] = dataDict['TOS126_new']
            # self.app.refresh_plot()            
        else:
            print('NO TOS')
            # self.app.tos_loaded_fullRes = tosFullRes
            # self.app.init_plot()
        
        self.app.adding_new_data = False
        self.app.init_ctrl_points()
        self.app.init_tos_line()
        self.app.refresh_plot()