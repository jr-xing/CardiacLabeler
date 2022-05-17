# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 13:07:03 2020

@author: Jerry Xing
http://zetcode.com/gui/pyqt5/
https://gist.github.com/peace098beat/db8ef7161508e6500ebe # Drag & Drop File
https://github.com/pyqtgraph/pyqtgraph
https://matplotlib.org/3.1.1/gallery/user_interfaces/embedding_in_qt_sgskip.html
https://www.learnpyqt.com/courses/graphics-plotting/plotting-matplotlib/
https://stackoverflow.com/questions/21654008/matplotlib-drag-overlapping-points-interactively
https://stackoverflow.com/questions/22376437/matplotlib-drawing-directly-on-the-canvas
https://doc.qt.io/qtforpython/overviews/dnd.html # drag & drop
https://medium.com/@mahmoudahmed_92535/pyqt5-best-css-styles-8554263b2599
https://pyside-material.readthedocs.io/en/latest/
"""
#%%
import sys
from PyQt5 import QtWidgets
from components.main_window import MainWindow
    
app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()
