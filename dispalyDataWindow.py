#!/usr/bin/env python
#-*-coding:utf-8 -*-

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer

import signal, sys
import array, os
import displayDataParseThread

dirname = os.path.dirname(pg.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')  

class DisplayDataWindow(QWidget):
    def __init__(self):
        super(DisplayDataWindow,self).__init__()
        # signal.signal(signal.SIGINT, self.sig_handler)
        # signal.signal(signal.SIGTERM, self.sig_handler)
        
        desktop = QtWidgets.QApplication.desktop()
        screenRect = desktop.screenGeometry()
        height = screenRect.height()
        width = screenRect.width()    
        
        self.win = pg.GraphicsLayoutWidget(show=False)
        self.win.setWindowTitle('display data window')
        self.win.resize(width, height)
        self.pw.setTitle('Data analysis Chart')           # 表格的名字
        self.pw.showGrid(x=True, y=True)  # 把X和Y的表格打开

        # 1) Simplest approach -- update data in the array such that plot appears to scroll
        #    In these examples, the array size is fixed.
        self.pw = self.win.addPlot()     # 把图pw加入到窗口中
        self.pw.setDownsampling(mode='peak')
        self.pw.setClipToView(True)
        self.pw.setLabel('bottom', 'Time', 'ms')
        self.pw.setLabel('left', 'data', 'l')
        # self.pw.setRange(xRange=[0, self.historyLength], yRange=[-1000, 1000], padding=0)
        
        self.historyLength = 300            # 横坐标长度
        self.data_mc = array.array('i')     # 可动态改变数组的大小,int型数组 'd' double类型数组
        self.data_fo1 = array.array('i')
        self.data_fo2 = array.array('i')
        self.curve_num = 3

        # self.data1 = np.random.normal(size=300)
        # self.data2 = np.random.normal(size=300)
        # self.data3 = np.random.normal(size=300)
        # self.curve1 = self.pw.plot(self.data1)
        # self.curve2 = self.pw.plot(self.data2)
        # self.curve3 = self.pw.plot(self.data3)

        self.data_mc = np.zeros(self.historyLength).__array__('d')       # 把数组长度定下来
        self.data_fo1 = np.zeros(self.historyLength).__array__('d')
        self.data_fo2 = np.zeros(self.historyLength).__array__('d')
        
        self.curve = self.pw.plot(self.data_mc, pen='r')        # 绘制一个图形
        self.curve1 = self.pw.plot(self.data_fo1, pen='g')
        self.curve2 = self.pw.plot(self.data_fo2, pen='b')
        self.ptr = 0

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
         
    def update(self):

        # self.data1[:-1] = self.data1[1:]  # shift data in the array one sample left        
        # self.data1[-1] = np.random.normal() + 3     # (see also: np.roll)
        
        # self.data2[:-1] = self.data2[1:]  # shift data in the array one sample left        
        # self.data2[-1] = np.random.normal()
        
        # self.data3[:-1] = self.data3[1:]  # shift data in the array one sample left        
        # self.data3[-1] = np.random.normal() + 5

        # self.curve1.setData(self.data1, pen="r")
        # self.curve1.setPos(self.ptr, 0)
        # self.curve2.setData(self.data2, pen="g")
        # self.curve2.setPos(self.ptr, 0)
        # self.curve3.setData(self.data3, pen="b")
        # self.curve3.setPos(self.ptr, 0)
        # self.ptr += 1
        self.plotData()

    def sig_handler(self, signum, frame):
        sys.exit(0)

    def plotData(self):
        displayDataParseThread.displayData_lock.acquire()
        if self.ptr < self.historyLength:
            self.data_mc[self.ptr] = displayDataParseThread.mutualCapacitanceQueue.get()
            if self.curve_num >= 2:
                self.data_fo1[self.ptr] = displayDataParseThread.threeDimensionalForcesOutside1.get()
            if self.curve_num >= 3:
                self.data_fo2[self.ptr] = displayDataParseThread.threeDimensionalForcesOutside2.get()
        else:
            self.data_mc[:-1] = self.data_mc[1:]
            self.data_mc[self.ptr-1] = displayDataParseThread.mutualCapacitanceQueue.get()
            if self.curve_num >= 2:
                self.data_fo1[:-1] = self.data_fo1[1:]
                self.data_fo1[self.ptr-1] = displayDataParseThread.threeDimensionalForcesOutside1.get()
            if self.curve_num >= 3:
                self.data_fo2[:-1] = self.data_fo2[1:]
                self.data_fo2[self.ptr-1] = displayDataParseThread.threeDimensionalForcesOutside2.get()
        displayDataParseThread.displayData_lock.acquire()

        self.curve.setData(self.data_mc, pen="r")
        self.curve.setPos(self.ptr, 0)
        self.curve1.setData(self.data_fo1, pen="g")
        self.curve1.setPos(self.ptr, 0)
        self.curve2.setData(self.data_fo2, pen="b")
        self.curve2.setPos(self.ptr, 0)
        self.ptr += 1

    