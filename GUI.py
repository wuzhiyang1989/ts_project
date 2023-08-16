# coding:utf-8

import sys
import os
from PIL import Image
import numpy as np

from queue import Queue
from threading import Lock
from time import sleep
from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QStackedWidget, QFrame, QWidget, QHBoxLayout, QFileDialog, QMessageBox, QComboBox
from PyQt5.QtWidgets import (QPushButton, QApplication, QDesktopWidget)
from PyQt5.QtGui import QIcon,QFont
from PyQt5.QtCore import QCoreApplication, Qt, QTimer

import UartReceiveThread, URRobotThread
import dispalyDataWindow

quitApplication = 0
sendMessageQueue = Queue(maxsize=10)
send_lock = Lock()
stateMachine_Lock = Lock()

runState = 0        # 0: stop; 1: run
displayPictureName = "Nothing"

class MainUi(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.display_win = dispalyDataWindow.DisplayDataWindow()

    def init_ui(self):
        #获取显示器分辨率大小
        self.desktop = QtWidgets.QApplication.desktop()
        self.screenRect = self.desktop.screenGeometry()
        self.height = self.screenRect.height()
        self.width = self.screenRect.width()

        self.setWindowTitle('TASHAN')
        self.setWindowIcon(QIcon('./images-new/LOGO.png'))

        # 主窗口及布局
        self.setFixedSize(self.width, self.height)
        self.main_widget = QtWidgets.QWidget()                  # 创建窗口主部件
        self.main_layout = QtWidgets.QGridLayout()              # 创建主部件的网格布局
        self.main_widget.setLayout(self.main_layout)            # 设置窗口主部件布局为网格布局
        self.main_widget.setFixedSize(self.width, self.height)  # 禁止调整窗口大小
        
        # top部件及布局
        self.top_widget = QtWidgets.QWidget()       
        self.top_widget.setObjectName('top_widget')
        self.top_layout = QtWidgets.QGridLayout()       # 创建左侧部件的网格布局层
        self.top_widget.setLayout(self.top_layout)      # 设置左侧部件布局为网格

        # bottom 部件及布局
        self.bottom_Widget = QtWidgets.QWidget()
        self.bottom_Widget.setObjectName('bottom_Widget')
        self.bottom_layout = QtWidgets.QGridLayout()    
        self.bottom_Widget.setLayout(self.bottom_layout)

        self.main_layout.addWidget(self.top_widget, 0, 0, 10, 12)            # 左侧部件在第0行第0列，占8行3列
        self.main_layout.addWidget(self.bottom_Widget, 10, 0, 2, 12)         # 右侧部件在第0行第3列，占8行9列
        self.setCentralWidget(self.main_widget)                              # 设置窗口主部件,中心窗口

        self.logo_label = QtWidgets.QLabel(self)
        self.logo_label.setGeometry(QtCore.QRect(0, 0, 352, 116))            # setGeometry(左右， 上下， 宽， 高)
        self.logo_label.setText("")
        self.logo_label.setObjectName("Logo")

        logo_img = os.path.abspath('images-new/LOGO.png')
        image = QtGui.QPixmap(logo_img).scaled(500, 500)           # 按指定路径找到图片
        self.logo_label.setPixmap(image)                           # 在label上显示图片
        self.logo_label.setStyleSheet("border: 0.3px solid gray")
        self.logo_label.setScaledContents(True)                    # 让图片自适应label大小

        self.left_button_1 = QtWidgets.QPushButton()
        self.left_button_1.setObjectName('left_button')
        self.left_button_2 = QtWidgets.QPushButton()
        self.left_button_2.setObjectName('left_button')
        self.left_button_3 = QtWidgets.QPushButton()
        self.left_button_3.setObjectName('left_button')
        self.left_button_4 = QtWidgets.QPushButton()
        self.left_button_4.setObjectName('left_button')
        self.left_button_5 = QtWidgets.QPushButton()
        self.left_button_5.setObjectName('left_button')
        self.left_button_6 = QtWidgets.QPushButton()
        self.left_button_6.setObjectName('left_button')
        self.left_button_7 = QtWidgets.QPushButton()
        self.left_button_7.setObjectName('left_button')
        self.left_button_8 = QtWidgets.QPushButton()
        self.left_button_8.setObjectName('left_button')
        self.left_button_9 = QtWidgets.QPushButton()
        self.left_button_9.setObjectName('left_button')
        self.left_button_10 = QtWidgets.QPushButton()
        self.left_button_10.setObjectName('left_button')
        self.left_button_11 = QtWidgets.QPushButton()
        self.left_button_11.setObjectName('left_button')
        self.left_button_12 = QtWidgets.QPushButton()
        self.left_button_12.setObjectName('left_button')

        self.left_button_1.setDisabled(True)
        self.left_button_2.setDisabled(True)
        self.left_button_3.setDisabled(True)
        self.left_button_4.setDisabled(True)
        self.left_button_5.setDisabled(True)
        self.left_button_6.setDisabled(True)
        self.left_button_7.setDisabled(True)
        self.left_button_8.setDisabled(True)
        self.left_button_9.setDisabled(True)
        self.left_button_10.setDisabled(True)
        self.left_button_11.setDisabled(True)
        self.left_button_12.setDisabled(True)
        
        self.start = QtWidgets.QPushButton("Start")  
        self.start.setObjectName('left_label')
        self.start.clicked.connect(self.startBtnCallback)

        self.data = QtWidgets.QPushButton("Data analysis")  
        self.data.setObjectName('left_label')
        self.data.clicked.connect(self.toggle_window)

        self.stop = QtWidgets.QPushButton("Stop")  
        self.stop.setObjectName('left_label')
        self.stop.clicked.connect(self.stopBtnCallback)

        self.bottom_layout.addWidget(self.left_button_1, 10, 0, 1, 1)
        self.bottom_layout.addWidget(self.left_button_2, 10, 1, 1, 1)
        self.bottom_layout.addWidget(self.left_button_3, 10, 2, 1, 1)
        self.bottom_layout.addWidget(self.left_button_4, 10, 3, 1, 1)
        self.bottom_layout.addWidget(self.start, 10, 4, 1, 1)
        self.bottom_layout.addWidget(self.left_button_5, 10, 5, 1, 1)
        self.bottom_layout.addWidget(self.left_button_6, 10, 6, 1, 1)
        self.bottom_layout.addWidget(self.data, 10, 7, 1, 1)
        self.bottom_layout.addWidget(self.left_button_7, 10, 8, 1, 1)
        self.bottom_layout.addWidget(self.left_button_8, 10, 9, 1, 1)
        self.bottom_layout.addWidget(self.stop, 10, 10, 1, 1)
        self.bottom_layout.addWidget(self.left_button_9, 10, 11, 1, 1)
        self.bottom_layout.addWidget(self.left_button_10, 10, 12, 1, 1)
        self.bottom_layout.addWidget(self.left_button_11, 10, 13, 1, 1)
        self.bottom_layout.addWidget(self.left_button_12, 10, 14, 1, 1)

        self.bm1 = self.readImage(r'images-new/夹爪中没有物品.png')
        self.bm2 = self.readImage(r'images-new/夹爪自适应抓取中.png')
        self.bm3 = self.readImage(r'images-new/夹爪中感应有物体.png')
        self.bm4 = self.readImage(r'images-new/夹爪中物体在滑动.png')
        self.bm5 = self.readImage(r'images-new/夹爪抓取物体相对稳定.png')
        self.bm6 = self.readImage(r'images-new/夹爪中物品脱落.png')

        self.gripper_label = QtWidgets.QLabel(self)
        self.gripper_label.setGeometry(QtCore.QRect(int((self.width-385)/2), 120, 385, 544))    # setGeometry(左右， 上下， 宽， 高)
        self.gripper_label.setText("")
        self.gripper_label.setObjectName("Gripper")
        self.gripper_label.setPixmap(self.bm1)                           # 在label上显示图片
        self.gripper_label.setStyleSheet("border: 0.3px solid gray")
        self.gripper_label.setScaledContents(True)

        self.setStyleSheet("background-color: white;")         # 主窗口美化
        self.setWindowOpacity(1)                               # 设置窗口透明度
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)      # 隐藏边框
        self.main_layout.setSpacing(0)                         # 去除左侧部件和右侧部件中的缝隙

         # top部件菜单美化及整体美化
        self.top_widget.setStyleSheet('''
            QPushButton{border:none;color:white;}
            QPushButton#left_label{
                border:none;
                border-bottom:1px solid SteelBlue;
                font-size:32px;
                font-weight:700;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
            QPushButton#left_button:hover{border-left:4px solid red;font-weight:700;}
            
            QWidget#top_widget{
                background:white;
                border-top:1px solid white;
                border-bottom:1px solid white;
                border-left:1px solid white;
                border-top-left-radius:5px;
                border-bottom-left-radius:5px;
            }
        ''')
        
        # bottom 框整体风格美化
        self.bottom_Widget.setStyleSheet('''
            QWidget#bottom_Widget{
                color:#232C51;
                background:SteelBlue;
                border-top:1px solid darkGray;
                border-bottom:1px solid darkGray;
                border-right:1px solid darkGray;
                border-top-right-radius:5px;
                border-bottom-right-radius:5px;
            }

            QPushButton{border:none;color:SteelBlue; background:SteelBlue;}                        
            QPushButton{
                border:none;
                color:darkGray;
                font-size:12px;
                height:40px;
                padding-left:5px;
                padding-right:10px;
                text-align:left;
            }
            QPushButton:hover{
                color:SteelBlue;
                border:1px solid #F3F3F5;
                border-radius:10px;
                background:LightGray;
            }
        
            QPushButton#left_label{
                border:none;
                border-bottom:1px solid SteelBlue;
                text-align:center;
                font-size:24px;
                font-weight:700;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }        

            QLabel#right_lable{
                border:none;
                font-size:16px;
                font-weight:700;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
        ''')
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.runTimer)
        self.timer.start(100)

    def readImage(self, image_path):
        image = Image.open(image_path)
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)         # 将图片转化成Qt可读格式
        image_resized = np.asarray(image_resized)
        image_height, image_width, image_depth = image_resized.shape
        qimage = QtGui.QImage(image_resized.data, image_width, image_height, image_width * image_depth, QtGui.QImage.Format_RGB888)
        qimage = QtGui.QPixmap(qimage).scaled(400, 400)      # 加载图片,并自定义图片展示尺寸
        return qimage

    def runTimer(self):
        if displayPictureName == "Nothing": #(t.tm_sec % 6 == 0):
            self.gripper_label.setPixmap(self.bm1)
        elif displayPictureName == "Something": #(t.tm_sec % 6 == 1):
            self.gripper_label.setPixmap(self.bm2)
        elif displayPictureName == "Grabbing": #(t.tm_sec % 6 == 2):
            self.gripper_label.setPixmap(self.bm3)
        elif displayPictureName == "Sliding": #(t.tm_sec % 6 == 3):
            self.gripper_label.setPixmap(self.bm4)
        elif displayPictureName == "Stable": #(t.tm_sec % 6 == 4):
            self.gripper_label.setPixmap(self.bm5)
        elif displayPictureName == "Dropped": #(t.tm_sec % 6 == 5):
            self.gripper_label.setPixmap(self.bm6)
        
    def startBtnCallback(self):
        global runState
        if runState == 0 and len(UartReceiveThread.port_list) > 0:
            runState = 1
            print('startBtnCallback')

    def returnKeyCallback(self):
        self.startBtnCallback()
        print('--returnKeyCallback')

    def stopBtnCallback(self):
        global runState, stateMachine_Lock
        if runState == 1:
            stateMachine_Lock.acquire()
            URRobotThread.stateMachine = "Btn_UI_Stop"
            stateMachine_Lock.release()
            send_lock.acquire()
            sendMessageQueue.put("stopBtn")
            send_lock.release()
            runState = 0
            print('stopBtnCallback')
    
    def spaceKeyCallback(self):
        self.stopBtnCallback()
        print('--spaceKeyCallback')

    def backSpaceKeyCallback(self):
        send_lock.acquire()
        sendMessageQueue.put("MutualCapacitanceClean")
        send_lock.release()
        print('backSpaceKeyCallback')

    def resize(self, w, h, w_box, h_box, pil_image):
        f1 = 1.0 * w_box / w  # 1.0 forces float division in Python2
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.Resampling.LANCZOS)

    def quitApp(self):
        global quitApplication, stateMachine_Lock

        self.stopBtnCallback()
        sleep(1)

        print('quitApp')
        quitApplication = 1
        sleep(1)

        print('exit success!')
        self.display_win.win.close()
        self.display_win.close()
        self.close()

    def closeEvent(self, event):    # 事件处理, 重写点X关闭的方法
        reply = QMessageBox.question(self, 'Message!',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        # 这里event.key（）显示的是按键的编码! 举例: Qt.Key_A注意虽然字母大写，但按键事件对大小写不敏感
        if event.key() == Qt.Key_Escape:    # ESC退出程序
            self.quitApp()
        if event.key() == Qt.Key_F2:        # F2最小化窗口
            self.showMinimized()
        if event.key() == Qt.Key_A:         # A全屏显示窗口
            self.showFullScreen()
        if event.key() == Qt.Key_Enter - 1:     # Enter启动视触融合程序运行
            self.returnKeyCallback()
        if event.key() == Qt.Key_Space:         # 空格键停止机械臂程序运行
            self.spaceKeyCallback()
        if event.key() == Qt.Key_Backspace:     # 退格键清除电容值
            self.backSpaceKeyCallback()

    def toggle_window(self, checked):
        if self.display_win.isVisible():
            self.display_win.hide()
        else:
            self.display_win.win.show()

def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = MainUi()
    gui.show()
    sys.exit(app.exec_())




