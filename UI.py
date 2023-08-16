# -*- coding: utf-8 -*-

import tkinter as tk
import URRobotThread
from queue import Queue
from PIL import Image, ImageTk
from time import sleep
from threading import Lock
import UartReceiveThread

quitApplication = 0
sendMessageQueue = Queue(maxsize=10)
send_lock = Lock()
stateMachine_Lock = Lock()

runState = 0        # 0: stop; 1: run
displayPictureName = "Nothing"

class FullscreenExample:

    def __init__(self):
        self.window = tk.Tk()
        self.window.config(background = "#E6E6E6")
        self.window.attributes('-fullscreen', True)
        self.fullScreenState = False
        self.window.bind("<F11>", self.toggleFullScreen)
        self.window.bind("<Escape>",  self.quitApp)
        self.window.bind("<Return>", self.returnKeyCallback)
        self.window.bind("<space>", self.spaceKeyCallback)
        self.window.bind("<BackSpace>", self.backSpaceKeyCallback)

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        w_bt = 200
        h_bt = 100
        gap_bt = (screen_width - 3 * w_bt) / 4

        pil_image_start = Image.open(r'images-new/start.png')
        w, h = pil_image_start.size
        pil_image_start_resized = self.resize(w, h, w_bt, h_bt, pil_image_start)
        tk_image_start = ImageTk.PhotoImage(pil_image_start_resized)
        startBtn = tk.Button(self.window, image = tk_image_start, width = w_bt, height = h_bt, borderwidth = 0, command = self.startBtnCallback)  # 设置调用函数
        startBtn.place(x = gap_bt, y = screen_height - 150)

        # pil_image_back = Image.open(r'images-new/back.png')
        # w, h = pil_image_back.size
        # pil_image_back_resized = self.resize(w, h, w_bt, h_bt, pil_image_back)
        # tk_image_back = ImageTk.PhotoImage(pil_image_back_resized)
        # backBtn = tk.Button(self.window, image = tk_image_back, width = w_bt, height = h_bt, borderwidth = 0, command = self.backBtnCallback)  # 设置调用函数
        # backBtn.place(x = gap_bt * 2 + w_bt, y = screen_height - 150)

        pil_image_stop = Image.open(r'images-new/stop.png')
        w, h = pil_image_stop.size
        pil_image_stop_resized = self.resize(w, h, w_bt, h_bt, pil_image_stop)
        tk_image_stop = ImageTk.PhotoImage(pil_image_stop_resized)
        stopBtn = tk.Button(self.window, image=tk_image_stop, width=w_bt, height=h_bt, borderwidth=0, command=self.stopBtnCallback)  # 设置调用函数
        stopBtn.place(x=gap_bt * 3 + w_bt * 2, y=screen_height - 150)

        image = Image.open(r'images-new/夹爪中没有物品.png')
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)
        self.bm1 = ImageTk.PhotoImage(image_resized)
        image = Image.open(r'images-new/夹爪自适应抓取中.png')
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)
        self.bm2 = ImageTk.PhotoImage(image_resized)
        image = Image.open(r'images-new/夹爪中感应有物体.png')
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)
        self.bm3 = ImageTk.PhotoImage(image_resized)
        image = Image.open(r'images-new/夹爪中物体在滑动.png')
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)
        self.bm4 = ImageTk.PhotoImage(image_resized)
        image = Image.open(r'images-new/夹爪抓取物体相对稳定.png')
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)
        self.bm5 = ImageTk.PhotoImage(image_resized)
        image = Image.open(r'images-new/夹爪中物品脱落.png')
        w, h = image.size
        image_resized = self.resize(w, h, 400, 550, image)
        self.bm6 = ImageTk.PhotoImage(image_resized)
        self.label = tk.Label(self.window, image=self.bm1, borderwidth=0, width= 385, height= 544)
        self.label.place(x = (screen_width - 385) / 2, y = 120)

        canvasLogo = tk.Canvas(self.window, width=352, height=116, bg='white')
        imageLogo = Image.open(r'images-new/LOGO.png')
        w, h = imageLogo.size
        imageLogo_resized = self.resize(w, h, 352, 116, imageLogo)
        imLogo = ImageTk.PhotoImage(imageLogo_resized)
        canvasLogo.create_image(176, 58, image=imLogo)  # 使用create_image将图片添加到Canvas组件中
        canvasLogo.place(x = 0, y = 0)

        self.runTimer()
        self.window.mainloop()

    def runTimer(self):
        #now = time.strftime("%H:%M:%S")
        # print(now)
        #t = time.localtime()
        if displayPictureName == "Nothing": #(t.tm_sec % 6 == 0):
            self.label.configure(image=self.bm1)
        elif displayPictureName == "Something": #(t.tm_sec % 6 == 1):
            self.label.configure(image=self.bm2)
        elif displayPictureName == "Grabbing": #(t.tm_sec % 6 == 2):
            self.label.configure(image=self.bm3)
        elif displayPictureName == "Sliding": #(t.tm_sec % 6 == 3):
            self.label.configure(image=self.bm4)
        elif displayPictureName == "Stable": #(t.tm_sec % 6 == 4):
            self.label.configure(image=self.bm5)
        elif displayPictureName == "Dropped": #(t.tm_sec % 6 == 5):
            self.label.configure(image=self.bm6)
        self.window.after(100, self.runTimer)

    def startBtnCallback(self):
        global runState
        if runState == 0 and len(UartReceiveThread.port_list) > 0:
            runState = 1
            print('startBtnCallback')

    def returnKeyCallback(self, event):
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

    def spaceKeyCallback(self, event):
        self.stopBtnCallback()
        print('--spaceKeyCallback')

    def backSpaceKeyCallback(self, event):
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
        return pil_image.resize((width, height), Image.ANTIALIAS)

    def toggleFullScreen(self, event):
        self.fullScreenState = not self.fullScreenState
        self.window.attributes("-fullscreen", self.fullScreenState)

    def quitApp(self, event):
        global quitApplication, stateMachine_Lock

        self.stopBtnCallback()
        sleep(1)

        print('quitApp')
        quitApplication = 1
        sleep(1)

        print('exit success!')
        self.window.destroy()

        
