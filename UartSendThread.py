import Utility, GUI, cameraDetection
import UartReceiveThread
from threading import Thread
from time import sleep

class UartSendThread(Thread):
    def __init__(self):
        self.sendcount = 0
        self.fingerNum = 0x02
        self.packPos = 0
        self.packBuf = [0] * 16
        Thread.__init__(self)

    def getCheckSum(self, buf, len):
        sum = 0
        for i in range(len):
            sum += buf[i]
        return sum & 0xFF
    
    def sendSplitData(self, data, len):
        dataPack = 0
        dataLess = 0
        dataPack = int(len / 3)
        dataLess = len % 3
        if (not data) or (len == 0):
            print("Data is NULL  ")
        if dataPack == 2:
            self.packBuf = [0] * 12
        if dataPack == 3 or dataPack == 4:
            self.packBuf = [0] * 16

        for packIndex in range(dataPack):
            self.packBuf[packIndex * 4] = self.fingerNum
            self.packBuf[(packIndex * 4) + 1] = data[self.packPos]
            self.packPos += 1
            self.packBuf[(packIndex * 4) + 2] = data[self.packPos]
            self.packPos += 1
            self.packBuf[(packIndex * 4) + 3] = data[self.packPos]
            self.packPos += 1

        if dataLess > 0:
            self.packBuf[dataPack * 4] = self.fingerNum
            if dataLess == 1:
                self.packBuf[(dataPack * 4) + 1] = data[self.packPos]
                self.packPos += 1
                self.packBuf[(dataPack * 4) + 2] = 0xFF
                self.packPos += 1
                self.packBuf[(dataPack * 4) + 3] = 0xFF
                self.packPos += 1
            if dataLess == 2:
                self.packBuf[(dataPack * 4) + 1] = data[self.packPos]
                self.packPos += 1
                self.packBuf[(dataPack * 4) + 2] = data[self.packPos]
                self.packPos += 1
                self.packBuf[(dataPack * 4) + 3] = 0xFF
                self.packPos += 1
            UartReceiveThread.uart.write(self.packBuf)   
            
        else:
            UartReceiveThread.uart.write(self.packBuf)
            
        if dataPack == 2:
            self.packBuf = [0] * 12
            self.packPos = 0
        if dataPack == 3 or dataPack == 4:
            self.packBuf = [0] * 16 
            self.packPos = 0

    def run(self):
        while GUI.quitApplication == 0:
            n = GUI.sendMessageQueue.qsize()
            if n > 0:
                cmd = ""
                GUI.send_lock.acquire()
                if not GUI.sendMessageQueue.empty():
                    cmd = GUI.sendMessageQueue.get()
                GUI.send_lock.release()
                len = 10
                if cmd == "StartPrepare":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0x01, 0xE8]

                    if cameraDetection.obj.label == "stand_bottle":
                        data[7] = 0x01
                    elif cameraDetection.obj.label == "stand_sponge":
                        data[7] = 0x02
                    elif cameraDetection.obj.label == "stand_glass":
                        data[7] = 0x03
                    elif cameraDetection.obj.label == "wood":
                        data[7] = 0x04
                    elif cameraDetection.obj.label == "stand_paper":
                        data[7] = 0x05
                    elif cameraDetection.obj.label == "mouse_box":
                        data[7] = 0x06
                    elif cameraDetection.obj.label == "acrylic_plate":
                        data[7] = 0x07
        
                elif cmd == "StartGrab":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0x02, 0xE9]
                elif cmd == "MoveComplete":
                    data = [0x55, 0xAA, 0x04, 0xE3, 0x00, 0x00, 0x02, 0x00, 0x0F, 0xF7]
                elif cmd == "upReply_GrabComplete":
                    data = [0x55, 0xAA, 0x04, 0xE3, 0x00, 0x00, 0x02, 0x00, 0x02, 0xE8]
                elif cmd == "LiftComplete":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0xF3, 0xDA]
                elif cmd == "StartDecline":
                    data = [0x55, 0xAA, 0x04, 0xE1, 0x00, 0x00, 0x00, 0xE4]
                    len = 8
                elif cmd == "CompleteDecline":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0x03, 0xEA]
                elif cmd == "stopBtn":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0xF0, 0xD7]
                elif cmd == "HandInteraction":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0xF2, 0xD9]
                elif cmd == "MutualCapacitanceClean": # 55 AA 04 E2 00 00 02 00 FA E1
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0xFA, 0xE1]
                elif cmd == "CapacitiveReset":
                    data = [0x55, 0xAA, 0x06, 0xE5, 0x00, 0x00, 0x01, 0x02, 0xED]
                    len = 9
              
                data[4] = (self.sendcount & 0xFF00) >> 8
                data[5] = self.sendcount & 0x00FF
                data[len - 1] = self.getCheckSum(data, len - 1)
                
                if len == 9:
                    UartReceiveThread.ser.write(data)
                    strbuf = " << Send >> " + str(data)
                    Utility.formatPrinting(strbuf)
                else:
                    self.sendSplitData(data, len)
                    # UartReceiveThread.uart.write(data)
                strbuf = " << SendThread >> " + cmd
                Utility.formatPrinting(strbuf)
                self.sendcount += 1
                if self.sendcount == 0x10000:
                    self.sendcount = 0
            sleep(0.01)

        print("UartSendThread quit")
       
