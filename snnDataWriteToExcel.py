import UartReceiveThread, GUI
from threading import Thread
from time import sleep, time
import openpyxl, datetime
import cameraDetection, URRobotThread

# 创建Excel工作簿和获取默认的工作表
workbook = openpyxl.Workbook()
sheet = workbook.active

class SnnDataWriteToExcel(Thread):
    def __init__(self):
        self.packPos = 0
        self.packBuf = [0]*90
        self.snnClass = ""
        Thread.__init__(self)
        self.start()

    def getCheckSum(self, buf, len):
        sum = 0
        for i in range(len):
            if i % 2 == 0:
                sum += buf[i]
            else:
                sum += (buf[i] * 256)
        return sum & 0xFFFF
    
    def run(self):
        readLen = 0
        row = 1

        t = datetime.datetime.fromtimestamp(time())
        while GUI.quitApplication == 0:
            n = UartReceiveThread.snnDataReceiveBuffer.qsize()
            readLen = 0

            # 在抓取物品过程中，采集数据。在夹爪准备好的子任务3，开始保存数据，保存在一个文件中。
            if (URRobotThread.task_num == 1) and (URRobotThread.task_sub_step == 3):  #this_message == "downSend_PrepareComplete"
                t = datetime.datetime.fromtimestamp(time())
                row = 1
            
            if cameraDetection.obj.label == "stand_bottle":
                self.snnClass = "Plastic"
            elif cameraDetection.obj.label == "stand_sponge":
                self.snnClass = "Sponge"
            elif cameraDetection.obj.label == "stand_glass":
                self.snnClass = "Glass"
            elif cameraDetection.obj.label == "wood":
                self.snnClass = "Wood"
                
            if n >= 4:
                for i in range(4):
                    UartReceiveThread.ReceiveBuffer_lock.acquire()
                    data = UartReceiveThread.snnDataReceiveBuffer.get()
                    UartReceiveThread.ReceiveBuffer_lock.release()
                    if data == 0x55 and self.packPos == 0:
                        len = 0
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0xAA and self.packPos == 1:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0x01 and self.packPos == 2:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0x27 and self.packPos == 3:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                        if data == 0x27:
                            len = 84
                            readLen = 80
  
            if readLen > 0:
                n = UartReceiveThread.snnDataReceiveBuffer.qsize()
                while n < readLen:
                    sleep(0.001)
                    n = UartReceiveThread.snnDataReceiveBuffer.qsize()

                if n >= readLen:
                    for i in range(readLen):
                        UartReceiveThread.ReceiveBuffer_lock.acquire()
                        data = UartReceiveThread.snnDataReceiveBuffer.get()
                        UartReceiveThread.ReceiveBuffer_lock.release()
                        if len > 0 and self.packPos < len:
                            self.packBuf[self.packPos] = data
                            self.packPos += 1
                            if len == self.packPos:
                                self.packPos = 0
                                checksum = self.getCheckSum(self.packBuf, len - 2)
                                
                                if checksum == (self.packBuf[len - 1] * 256) + self.packBuf[len - 2]:
                                    snnData = 0
                                    column = 1
                                    for num in range(4, 82):
                                        if num % 2 == 0:
                                            snnData += self.packBuf[num]
                                        else:
                                            snnData += (self.packBuf[num] * 256)
                                            sheet.cell(row=row, column=column).value = snnData
                                            column += 1
                                            snnData = 0
                                    row += 1
                                    sheet.delete_rows(row, 100)
                                    workbook.save(self.snnClass + "-" + str(t) + ".xlsx")
 
                                else:
                                    print("snnData checksum error")
                        else:
                            self.packBuf = [0] * 90
                            self.packPos = 0
                            print("self.packBuf = [0]*90 ")
     
            sleep(0.01)
        print("SnnDataWriteToExcelThread quit")