import Utility, GUI
import UartReceiveThread
from threading import Thread, Lock
from time import sleep
from queue import Queue

receiveMessageQueue = Queue(maxsize=20)
receiveMessageQueue_lock = Lock()

moveSourceLock = Lock()
someThing = 0
moveSource = 0
gripperDistance = 10

class UartProtocolParseThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.packPos = 0
        self.packBuf = [0]*30

    def getCheckSum(self, buf, len):
        sum = 0
        for i in range(len):
            sum += buf[i]
        return sum & 0xFF
      
    def run(self):
        global receiveMessageQueue, someThing, gripperDistance, moveSource
        readLen = 0
        while GUI.quitApplication == 0:
            n = UartReceiveThread.dataReceiveBuffer.qsize()
            readLen = 0
            if n >= 4:
                for i in range(4):
                    UartReceiveThread.ReceiveBuffer_lock.acquire()
                    data = UartReceiveThread.dataReceiveBuffer.get()
                    UartReceiveThread.ReceiveBuffer_lock.release()
                    if data == 0x55 and self.packPos == 0:
                        len = 0
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0xAA and self.packPos == 1:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0x03 and self.packPos == 2:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif (data == 0xE1 or data == 0xE2 or data == 0xE3 or data == 0xE4) and self.packPos == 3:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                        if data == 0xE1:
                            len = 8
                            readLen = 4
                        else:
                            len = 10
                            readLen = 6
            if readLen > 0:
                n = UartReceiveThread.dataReceiveBuffer.qsize()
                while n < readLen:
                    sleep(0.001)
                    n = UartReceiveThread.dataReceiveBuffer.qsize()

                if n >= readLen:
                    for i in range(readLen):
                        UartReceiveThread.ReceiveBuffer_lock.acquire()
                        data = UartReceiveThread.dataReceiveBuffer.get()
                        UartReceiveThread.ReceiveBuffer_lock.release()
                        if len > 0 and self.packPos < len:
                            self.packBuf[self.packPos] = data
                            self.packPos += 1
                            if len == self.packPos:
                                self.packPos = 0
                                checksum = self.getCheckSum(self.packBuf, len - 1)
                                
                                if checksum == self.packBuf[len - 1]:
                                    if self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x01:
                                        rm = "downReply_StartPrepare"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0xF4:
                                        rm = "downSend_PrepareGrabDemo"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x01:
                                        rm = "downSend_PrepareComplete"
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x02:
                                        rm = "downReply_StartGrab"
                                    elif self.packBuf[3] == 0xE4 and self.packBuf[6] == 0x02:
                                        someThing = self.packBuf[7]
                                        gripperDistance = self.packBuf[8]
                                        rm = "downSend_GripperState"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x02:
                                        rm = "downSend_GrabComplete"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x05:
                                        rm = "downSend_Shrink"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x06:
                                        rm = "downSend_Stable"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x07:
                                        rm = "downSend_loosen"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x08:
                                        rm = "downSend_FallDown"
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x10:
                                        rm = "downSend_RequestDecline"
                                    elif self.packBuf[3] == 0xE1 and self.packBuf[6] == 0x00:
                                        rm = "downReply_StartDecline"
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x03:
                                        rm = "downReply_CompleteDecline"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x03:
                                        rm = "downSend_GripperOpenComplete"
                                    elif self.packBuf[3] == 0xE3 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0xF0:
                                        rm = "downSend_TaskComplete"
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0xF0:
                                        rm = "downReply_UIStop"
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0xF2:
                                        rm = "downReply_HandInteraction"
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02  and self.packBuf[8] == 0x04:
                                        rm = "downSend_MoveLeft"
                                        moveSourceLock.acquire() 
                                        moveSource = self.packBuf[7]
                                        moveSourceLock.release()
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[8] == 0x05:
                                        rm = "downSend_MoveRight"
                                        moveSourceLock.acquire() 
                                        moveSource = self.packBuf[7]
                                        moveSourceLock.release()
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x06:
                                        rm = "downSend_HandStop"
                                        moveSourceLock.acquire() 
                                        moveSource = 0
                                        moveSourceLock.release()
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0x07:
                                        rm = "downSend_NoHandStop"
                                        moveSourceLock.acquire() 
                                        moveSource = 0
                                        moveSourceLock.release()
                                    elif self.packBuf[3] == 0xE2 and self.packBuf[6] == 0x02 and self.packBuf[7] == 0x00 and self.packBuf[8] == 0xFA:
                                        rm = "downReply_MutualCapacitanceClean"
                                    else:
                                        rm = ""

                                    if rm != "":
                                        receiveMessageQueue_lock.acquire()
                                        receiveMessageQueue.put(rm)
                                        receiveMessageQueue_lock.release()

                                    strbuf = "--- receiveMessageQueue --- " + rm 
                                    Utility.formatPrinting(strbuf)
                                else:
                                    print("checksum error")
                        else:
                            self.packBuf = [0] * 30
                            self.packPos = 0
                            print("self.packBuf = [0]*30 ")

            sleep(0.01)
        print("UartProtocolParseThread quit")
