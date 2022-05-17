from PyQt5 import QtCore as Qt
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QDrag, QImage
import matplotlib.patches as patches

class XEllipse(patches.Ellipse):
    def __init__(self, *args, **kwargs):
        super(XEllipse, self).__init__(*args, **kwargs)
        self.deactivated = False


class DraggableLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super(DraggableLabel, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        
    def mousePressEvent(self, event):
        # print('left click?')
        if event.button() == 1:# and self.geometry().contains(event.pos()):    
            # print('left click!')
            drag =  QDrag(self)
            mimeData =  Qt.QMimeData()
            print('formats',mimeData.formats())
    
            mimeData.setText('hh')
            drag.setMimeData(mimeData)
            print('formats',mimeData.formats())
            #drag.setPixmap(iconPixmap)
    
            dropAction = drag.exec_()
            print('dragged!')
            print(dropAction
            )
            print(drag)

class DraggablePoint:
    lock = None #only one can be animated at a time
    def __init__(self, point, app):
        self.point = point
        self.press = None
        self.background = None
        self.deactivated = False
        self.app = app

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.point.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = self.point.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = self.point.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.point.axes: return
        if DraggablePoint.lock is not None: return
        contains, attrd = self.point.contains(event)
        if not contains: return
        
        # self.app.refresh_plot()
        
        if event.button == 3:
            # right click
            self.point.deactivated = True
            self.app.refresh_plot()
            # self.app.update_plot()
            
            return
        
        self.press = (self.point.center), event.xdata, event.ydata
        DraggablePoint.lock = self

        # draw everything but the selected rectangle and store the pixel buffer
        canvas = self.point.figure.canvas
        #print(canvas = self.point.figure.canvas)
        axes = self.point.axes
        self.point.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.point.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.point)

        # and blit just the redrawn area
        canvas.blit(axes.bbox)
        
        # self.app.update_plot()

    def on_motion(self, event):
        if DraggablePoint.lock is not self:
            return
        if event.inaxes != self.point.axes: return
        self.point.center, xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.point.center = (max(self.point.center[0]+dx, 0.5), self.point.center[1]+dy)

        canvas = self.point.figure.canvas
        axes = self.point.axes
        # restore the background region
        canvas.restore_region(self.background)

        # redraw just the current rectangle
        axes.draw_artist(self.point)

        #print('MOVING!')
        self.app.update_tos_line()
        axes.draw_artist(self.app.tos_curve_line)
        # canvas.draw()

        # blit just the redrawn area
        canvas.blit(axes.bbox)
        
        

    def on_release(self, event):
        'on release we reset the press data'
        if DraggablePoint.lock is not self:
            return
        
        c = self.point.get_center()
        if c[0]<0.5:
            self.point.set_center(0.5, c[1])

        self.press = None
        DraggablePoint.lock = None

        # turn off the rect animation property and reset the background
        self.point.set_animated(False)
        self.background = None
        
        # self.app.tos_curve_line.set_color('b')
        # print("RELEASE!")
        self.app.update_plot()

        # redraw the full figure
        self.point.figure.canvas.draw()

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.point.figure.canvas.mpl_disconnect(self.cidpress)
        self.point.figure.canvas.mpl_disconnect(self.cidrelease)
        self.point.figure.canvas.mpl_disconnect(self.cidmotion)