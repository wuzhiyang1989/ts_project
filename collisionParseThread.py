import Utility, GUI
import UartReceiveThread
from threading import Thread, Lock
from time import sleep
from queue import Queue

collisionMessageQueue = Queue(maxsize=20)
collisionMessageQueue_lock = Lock()

class CollisionParseThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.packPos = 0
        self.packBuf = [0]*20
        self.start()

    def getCheckSum(self, buf, len):
        sum = 0
        for i in range(len):
            sum += buf[i]
        return sum & 0xFF
      
    def run(self):
        global collisionMessageQueue
        
        readLen = 0
        while GUI.quitApplication == 0:
            n = UartReceiveThread.collisionDataBuffer.qsize()
            readLen = 0
            if n >= 4:
                for i in range(4):
                    UartReceiveThread.collisionDataBuffer_lock.acquire()
                    data = UartReceiveThread.collisionDataBuffer.get()
                    UartReceiveThread.collisionDataBuffer_lock.release()
                    if data == 0x55 and self.packPos == 0:
                        len = 0
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0xAA and self.packPos == 1:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0x05 and self.packPos == 2:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                    elif data == 0xE4 and self.packPos == 3:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                        if data == 0xE4:
                            len = 16
                            readLen = 12
            
            if readLen > 0:
                n = UartReceiveThread.collisionDataBuffer.qsize()
                while n < readLen:
                    sleep(0.001)
                    n = UartReceiveThread.collisionDataBuffer.qsize()

                if n >= readLen:
                    for i in range(readLen):
                        UartReceiveThread.collisionDataBuffer_lock.acquire()
                        data = UartReceiveThread.collisionDataBuffer.get()
                        UartReceiveThread.collisionDataBuffer_lock.release()
                        if len > 0 and self.packPos < len:
                            self.packBuf[self.packPos] = data
                            self.packPos += 1
                            if len == self.packPos:
                                self.packPos = 0
                                checksum = self.getCheckSum(self.packBuf, len - 1)
                                if checksum == self.packBuf[len - 1]:
                                    if self.packBuf[7] == 0x00 and self.packBuf[11] == 0x00:
                                        cm = "downSend_NormalMove"
                                    elif self.packBuf[7] == 0x01 or self.packBuf[11] == 0x01:
                                        cm = "downSend_CollisionStop"
                                    else:
                                        cm = ""

                                    if cm != "":
                                        collisionMessageQueue_lock.acquire()
                                        collisionMessageQueue.put(cm)
                                        collisionMessageQueue_lock.release()
                                else:
                                    print(checksum, self.packBuf[len - 1],"checksum error")
                        else:
                            self.packBuf = [0] * 20
                            self.packPos = 0
                            print("self.packBuf = [0]*20 ")

            sleep(0.01)
        print("collisionParseThread quit")