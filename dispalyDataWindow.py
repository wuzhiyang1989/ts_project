#!/usr/bin/env python
#-*-coding:utf-8 -*-

import numpy as np
import pyqtgraph as pg
import os, displayDataParseThread

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QMainWindow, QLabel, QPushButton, QApplication, QMessageBox)
from PyQt5.QtCore import QCoreApplication, QTimer
from pyqtgraph import PlotWidget

dirname = os.path.dirname(pg.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')  

class DisplayDataWindow(QMainWindow):
    def __init__(self):
        self.dataIndex = 0               # 数据列表当前索引
        self.dataMaxLength = 1000        # 数据列表最大长度
        super(DisplayDataWindow,self).__init__()

        desktop = QtWidgets.QApplication.desktop()
        screenRect = desktop.screenGeometry()
        height = screenRect.height()
        width = screenRect.width() - 60 
             
        # self.win = pg.GraphicsLayoutWidget(show=False)
        # self.win.setWindowTitle('display data window')
        # self.win.resize(width, height)
        self.setFixedSize(width, height)
        self.main_widget = QtWidgets.QWidget()        # 创建窗口主部件
        self.main_layout = QtWidgets.QGridLayout()    # 创建主部件的网格布局
        self.main_widget.setLayout(self.main_layout)  # 设置窗口主部件布局为网格布局
        
        # 右侧部件及布局
        self.right_widget = QtWidgets.QWidget()               # 创建右侧部件
        self.right_widget.setObjectName('right_widget')
        self.right_layout = QtWidgets.QGridLayout()           # 创建右侧部件的网格布局层
        self.right_widget.setLayout(self.right_layout)        # 设置右侧部件布局为网格

        # 左侧部件及布局
        self.pw = PlotWidget()
        self.main_layout.addWidget(self.right_widget, 0, 11, 12, 1)           
        self.main_layout.addWidget(self.pw, 0, 0, 12, 11)                     
        self.setCentralWidget(self.main_widget)                              

        # 主窗口美化
        self.setWindowOpacity(1)                               # 设置窗口透明度
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)      # 隐藏边框
        self.main_layout.setSpacing(0)                         #去除左侧部件和右侧部件中的缝隙

        # 左侧部件的组件布局
        # 1. 顶部三个按钮
        self.right_close = QtWidgets.QPushButton("X")             # 关闭按钮
        self.right_visit = QtWidgets.QPushButton("▢")             # 空白按钮
        self.right_mini = QtWidgets.QPushButton("–")              # 最小化按钮
        self.right_close.clicked.connect(self.close)              # 关闭窗口
        self.right_visit.clicked.connect(self.showFullScreen)
        self.right_mini.clicked.connect(self.showMinimized)       # 最小化窗口

        self.checkBox = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox.setObjectName("checkBox")
        self.checkBox_1 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_1.setObjectName("checkBox")
        self.checkBox_2 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_2.setObjectName("checkBox")
        self.checkBox_3 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_3.setObjectName("checkBox")
        self.checkBox_4 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_4.setObjectName("checkBox")
        self.checkBox_5 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_5.setObjectName("checkBox")
        self.checkBox_6 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_6.setObjectName("checkBox")
        self.checkBox_7 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_7.setObjectName("checkBox")
        self.checkBox_8 = QtWidgets.QCheckBox(self.right_widget)
        self.checkBox_8.setObjectName("checkBox")
        self.right_button_9 = QtWidgets.QPushButton()
        self.right_button_9.setObjectName('left_button')
        self.right_button_10 = QtWidgets.QPushButton()
        self.right_button_10.setObjectName('left_button')
        self.right_button_11 = QtWidgets.QPushButton()
        self.right_button_11.setObjectName('left_button')
        self.right_button_12 = QtWidgets.QPushButton()
        self.right_button_12.setObjectName('left_button')

        self.right_button_9.setDisabled(True)
        self.right_button_10.setDisabled(True)
        self.right_button_11.setDisabled(True)
        self.right_button_12.setDisabled(True)

        self.right_layout.addWidget(self.right_mini, 0, 1, 1, 1)
        self.right_layout.addWidget(self.right_visit, 0, 2, 1, 1)
        self.right_layout.addWidget(self.right_close, 0, 3, 1, 1)
        self.right_layout.addWidget(self.checkBox, 2, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_1, 3, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_2, 4, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_3, 5, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_4, 6, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_5, 7, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_6, 8, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_7, 9, 0, 1, 3)
        self.right_layout.addWidget(self.checkBox_8, 10, 0, 1, 3)
        self.right_layout.addWidget(self.right_button_9, 11, 0, 1, 3)
        self.right_layout.addWidget(self.right_button_10, 12, 0, 1, 3)
        self.right_layout.addWidget(self.right_button_11, 13, 0, 1, 3)
        self.right_layout.addWidget(self.right_button_12, 14, 0, 1, 3)

        # self.pw = self.win.addPlot()
        self.pw.setDownsampling(mode='peak')
        self.pw.setClipToView(True)
        self.pw.setTitle('Data analysis Chart')           # 表格的名字
        self.pw.showGrid(x=True, y=True)  # 把X和Y的表格打开
        self.pw.setLabel('bottom', 'Time', 'ms')
        self.pw.setLabel('left', 'data', 'l')

        # 1. 左侧顶部三个按钮美化
        self.right_close.setFixedSize(25, 25)  # 设置关闭按钮的大小
        self.right_visit.setFixedSize(25, 25)  # 设置按钮大小
        self.right_mini.setFixedSize(25, 25)   # 设置最小化按钮大小
        self.right_close.setStyleSheet(
            '''QPushButton{background:#F76677;border-radius:5px;}QPushButton:hover{background:red;}''')
        self.right_visit.setStyleSheet(
            '''QPushButton{background:#F7D674;border-radius:5px;}QPushButton:hover{background:yellow;}''')
        self.right_mini.setStyleSheet(
            '''QPushButton{background:#6DDF6D;border-radius:5px;}QPushButton:hover{background:green;}''')

        # 2. 右侧部件菜单美化及整体美化
        self.right_widget.setStyleSheet('''
            QPushButton{border:none;color:black;}
            QCheckBox#checkBox{
                border:none;
                border-bottom:1px solid SteelBlue;
                font-size:20px;
                font-weight:700;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
            QPushButton#left_button:hover{border-left:4px solid red;font-weight:700;}
            
            QWidget#right_widget{
                background:SteelBlue;
                border-top:1px solid white;
                border-bottom:1px solid white;
                border-left:1px solid white;
                border-top-right-radius:10px;
                border-bottom-right-radius:10px;
            }
        ''')

        self.main_widget.setStyleSheet('''
            QWidget#main_widget{
                color:#232C51;
                background:darkGray;
                border-top:1px solid darkGray;
                border-bottom:1px solid darkGray;
                border-left:1px solid darkGray;
                border-top-left-radius:10px;
                border-bottom-left-radius:10px;
            }

            QLabel#right_lable{
                border:none;
                font-size:16px;
                font-weight:700;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
        ''')

        self.data_mc = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fo1 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fo2 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fo3 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fo4 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fi1 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fi2 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fi3 = np.zeros(self.dataMaxLength, dtype=float)
        self.data_fi4 = np.zeros(self.dataMaxLength, dtype=float)
        self.curve_num = 9

        self.curve = self.pw.plot(self.data_mc, pen=pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.SolidLine))        # 绘制一个图形
        self.curve1 = self.pw.plot(self.data_fi1, pen=pg.mkPen(color=(0, 255, 0), width=3, style=QtCore.Qt.SolidLine))
        self.curve2 = self.pw.plot(self.data_fi2, pen=pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.SolidLine))
        self.curve3 = self.pw.plot(self.data_fi3)
        self.curve4 = self.pw.plot(self.data_fi4, pen=pg.mkPen(color=(135, 206, 250), width=3, style=QtCore.Qt.SolidLine))
        self.curve5 = self.pw.plot(self.data_fo1, pen=pg.mkPen(color=(255, 215, 0), width=3, style=QtCore.Qt.SolidLine))
        self.curve6 = self.pw.plot(self.data_fo2, pen=pg.mkPen(color=(154, 50, 205), width=3, style=QtCore.Qt.SolidLine))
        self.curve7 = self.pw.plot(self.data_fo3, pen=pg.mkPen(color=(176, 48, 96), width=3, style=QtCore.Qt.SolidLine))
        self.curve8 = self.pw.plot(self.data_fo4, pen=pg.mkPen(color=(139, 105, 20), width=3, style=QtCore.Qt.SolidLine))
        
        self.retranslateUi()
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
            
    def update(self):
        self.plotData()
        # self.receiveData()

    def receiveData(self):      
        try:
            if self.dataIndex < self.dataMaxLength:
                # 接收到的数据长度小于最大数据缓存长度，直接按索引赋值，索引自增1
                self.data_mc[self.dataIndex] = float(displayDataParseThread.mutualCapacitanceQueue.get(block=False, timeout=3))
                self.data_fo1[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesOutside1.get(block=False, timeout=3))
                self.data_fo2[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesOutside2.get(block=False, timeout=3))
                self.data_fo3[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesOutside3.get(block=False, timeout=3))
                self.data_fo4[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesOutside4.get(block=False, timeout=3))
                self.data_fi1[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesInside1.get(block=False, timeout=3))
                self.data_fi2[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesInside2.get(block=False, timeout=3))
                self.data_fi3[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesInside3.get(block=False, timeout=3))
                self.data_fi4[self.dataIndex] = float(displayDataParseThread.threeDimensionalForcesInside4.get(block=False, timeout=3))
                self.dataIndex = self.dataIndex + 1
            else:
                # 寄收到的数据长度大于或等于最大数据缓存长度，丢弃最前一个数据新数据添加到数据列尾
                self.data_mc[:-1] = self.data_mc[1:]
                self.data_fo1[:-1] = self.data_fo1[1:]
                self.data_fo2[:-1] = self.data_fo2[1:]
                self.data_fo3[:-1] = self.data_fo3[1:]
                self.data_fo4[:-1] = self.data_fo4[1:]
                self.data_fi1[:-1] = self.data_fi1[1:]
                self.data_fi2[:-1] = self.data_fi2[1:]
                self.data_fi3[:-1] = self.data_fi3[1:]
                self.data_fi4[:-1] = self.data_fi4[1:]

                self.data_mc[self.dataIndex - 1] = float(displayDataParseThread.mutualCapacitanceQueue.get(block=False, timeout=3))
                self.data_fo1[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesOutside1.get(block=False, timeout=3))
                self.data_fo2[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesOutside2.get(block=False, timeout=3))
                self.data_fo3[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesOutside3.get(block=False, timeout=3))
                self.data_fo4[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesOutside4.get(block=False, timeout=3))
                self.data_fi1[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesInside1.get(block=False, timeout=3))
                self.data_fi2[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesInside2.get(block=False, timeout=3))
                self.data_fi3[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesInside3.get(block=False, timeout=3))
                self.data_fi4[self.dataIndex - 1] = float(displayDataParseThread.threeDimensionalForcesInside4.get(block=False, timeout=3))
        finally:   
            print("消息队列个数 ： ", displayDataParseThread.mutualCapacitanceQueue.qsize())
            # 更新波形数据
            if self.checkBox.isChecked():
                self.curve.setData(self.data_mc)
                self.curve.setPos(self.dataIndex, 0)
            if self.checkBox.isChecked() == False and self.checkBox.checkState() == 0:
                self.curve.clear()
            if self.checkBox_1.isChecked():
                self.curve1.setData(self.data_fi1)
                self.curve1.setPos(self.dataIndex, 0)
            if self.checkBox_1.isChecked() == False and self.checkBox_1.checkState() == 0:
                self.curve1.clear()
            if self.checkBox_2.isChecked():
                self.curve2.setData(self.data_fi2)
                self.curve2.setPos(self.dataIndex, 0)
            if self.checkBox_2.isChecked() == False and self.checkBox_2.checkState() == 0:
                self.curve2.clear()
            if self.checkBox_3.isChecked():
                self.curve3.setData(self.data_fi3, pen=pg.mkPen(color=(186, 85, 211), width=3, style=QtCore.Qt.SolidLine))
                self.curve3.setPos(self.dataIndex, 0)
            if self.checkBox_3.isChecked() == False and self.checkBox_3.checkState() == 0:
                self.curve3.clear()
            if self.checkBox_4.isChecked():
                self.curve4.setData(self.data_fi4)
                self.curve4.setPos(self.dataIndex, 0)
            if self.checkBox_4.isChecked() == False and self.checkBox_4.checkState() == 0:
                self.curve4.clear()
            if self.checkBox_5.isChecked():
                self.curve5.setData(self.data_fo1)
                self.curve5.setPos(self.dataIndex, 0)
            if self.checkBox_5.isChecked() == False and self.checkBox_5.checkState() == 0:
                self.curve5.clear()
            if self.checkBox_6.isChecked():
                self.curve6.setData(self.data_fo2)
                self.curve6.setPos(self.dataIndex, 0)
            if self.checkBox_6.isChecked() == False and self.checkBox_6.checkState() == 0:
                self.curve6.clear()
            if self.checkBox_7.isChecked():
                self.curve7.setData(self.data_fo3)
                self.curve7.setPos(self.dataIndex, 0)
            if self.checkBox_7.isChecked() == False and self.checkBox_7.checkState() == 0:
                self.curve7.clear()
            if self.checkBox_8.isChecked():
                self.curve8.setData(self.data_fo4)
                self.curve8.setPos(self.dataIndex, 0)
            if self.checkBox_8.isChecked() == False and self.checkBox_8.checkState() == 0:
                self.curve8.clear()

    def plotData(self):
        if self.dataIndex < self.dataMaxLength:
            self.data_mc[self.dataIndex] = displayDataParseThread.mutualCapacitanceQueue.get()
            if self.curve_num >= 2:
                self.data_fo1[self.dataIndex] = displayDataParseThread.threeDimensionalForcesOutside1.get()
            if self.curve_num >= 3:
                self.data_fo2[self.dataIndex] = displayDataParseThread.threeDimensionalForcesOutside2.get()
            if self.curve_num >= 4:
                self.data_fo3[self.dataIndex] = displayDataParseThread.threeDimensionalForcesOutside3.get()
            if self.curve_num >= 5:
                self.data_fo4[self.dataIndex] = displayDataParseThread.threeDimensionalForcesOutside4.get()
            if self.curve_num >= 6:
                self.data_fi1[self.dataIndex] = displayDataParseThread.threeDimensionalForcesInside1.get()
            if self.curve_num >= 7:
                self.data_fi2[self.dataIndex] = displayDataParseThread.threeDimensionalForcesInside2.get()
            if self.curve_num >= 8:
                self.data_fi3[self.dataIndex] = displayDataParseThread.threeDimensionalForcesInside3.get()
            if self.curve_num >= 9:
                self.data_fi4[self.dataIndex] = displayDataParseThread.threeDimensionalForcesInside4.get()
            self.dataIndex += 1    
        else:
            self.data_mc[:-1] = self.data_mc[1:]
            self.data_mc[self.dataIndex - 1] = displayDataParseThread.mutualCapacitanceQueue.get()
            if self.curve_num >= 2:
                self.data_fo1[:-1] = self.data_fo1[1:]
                self.data_fo1[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesOutside1.get()
            if self.curve_num >= 3:
                self.data_fo2[:-1] = self.data_fo2[1:]
                self.data_fo2[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesOutside2.get()
            if self.curve_num >= 4:
                self.data_fo3[:-1] = self.data_fo3[1:]
                self.data_fo3[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesOutside3.get()
            if self.curve_num >= 5:
                self.data_fo4[:-1] = self.data_fo4[1:]
                self.data_fo4[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesOutside4.get()
            if self.curve_num >= 6:
                self.data_fi1[:-1] = self.data_fi1[1:]
                self.data_fi1[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesInside1.get()
            if self.curve_num >= 7:
                self.data_fi2[:-1] = self.data_fi2[1:]
                self.data_fi2[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesInside2.get()
            if self.curve_num >= 8:
                self.data_fi3[:-1] = self.data_fi3[1:]
                self.data_fi3[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesInside3.get()
            if self.curve_num >= 9:
                self.data_fi4[:-1] = self.data_fi4[1:]
                self.data_fi4[self.dataIndex - 1] = displayDataParseThread.threeDimensionalForcesInside4.get()
      
        # 更新波形数据
        if self.checkBox.isChecked():
            self.curve.setData(self.data_mc)
            self.curve.setPos(self.dataIndex, 0)
        if self.checkBox.isChecked() == False and self.checkBox.checkState() == 0:
            self.curve.clear()
        if self.checkBox_1.isChecked():
            self.curve1.setData(self.data_fi1)
            self.curve1.setPos(self.dataIndex, 0)
        if self.checkBox_1.isChecked() == False and self.checkBox_1.checkState() == 0:
            self.curve1.clear()
        if self.checkBox_2.isChecked():
            self.curve2.setData(self.data_fi2)
            self.curve2.setPos(self.dataIndex, 0)
        if self.checkBox_2.isChecked() == False and self.checkBox_2.checkState() == 0:
            self.curve2.clear()
        if self.checkBox_3.isChecked():
            self.curve3.setData(self.data_fi3, pen=pg.mkPen(color=(186, 85, 211), width=3, style=QtCore.Qt.SolidLine))
            self.curve3.setPos(self.dataIndex, 0)
        if self.checkBox_3.isChecked() == False and self.checkBox_3.checkState() == 0:
            self.curve3.clear()
        if self.checkBox_4.isChecked():
            self.curve4.setData(self.data_fi4)
            self.curve4.setPos(self.dataIndex, 0)
        if self.checkBox_4.isChecked() == False and self.checkBox_4.checkState() == 0:
            self.curve4.clear()
        if self.checkBox_5.isChecked():
            self.curve5.setData(self.data_fo1)
            self.curve5.setPos(self.dataIndex, 0)
        if self.checkBox_5.isChecked() == False and self.checkBox_5.checkState() == 0:
            self.curve5.clear()
        if self.checkBox_6.isChecked():
            self.curve6.setData(self.data_fo2)
            self.curve6.setPos(self.dataIndex, 0)
        if self.checkBox_6.isChecked() == False and self.checkBox_6.checkState() == 0:
            self.curve6.clear()
        if self.checkBox_7.isChecked():
            self.curve7.setData(self.data_fo3)
            self.curve7.setPos(self.dataIndex, 0)
        if self.checkBox_7.isChecked() == False and self.checkBox_7.checkState() == 0:
            self.curve7.clear()
        if self.checkBox_8.isChecked():
            self.curve8.setData(self.data_fo4)
            self.curve8.setPos(self.dataIndex, 0)
        if self.checkBox_8.isChecked() == False and self.checkBox_8.checkState() == 0:
            self.curve8.clear()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.checkBox.setText(_translate("MainWindow", "mutualCapacitance"))
        self.checkBox_1.setText(_translate("MainWindow", "ForcesInside1"))
        self.checkBox_2.setText(_translate("MainWindow", "ForcesInside2"))
        self.checkBox_3.setText(_translate("MainWindow", "ForcesInside3"))
        self.checkBox_4.setText(_translate("MainWindow", "ForcesInside4"))
        self.checkBox_5.setText(_translate("MainWindow", "ForcesOutside1"))
        self.checkBox_6.setText(_translate("MainWindow", "ForcesOutside2"))
        self.checkBox_7.setText(_translate("MainWindow", "ForcesOutside3"))
        self.checkBox_8.setText(_translate("MainWindow", "ForcesOutside4"))

