import Utility, GUI
import UartReceiveThread
from threading import Thread, Lock
from time import sleep
from queue import Queue

mutualCapacitanceQueue = Queue(maxsize=1000)
threeDimensionalForcesInside1 = Queue(maxsize=1000)
threeDimensionalForcesInside2 = Queue(maxsize=1000)
threeDimensionalForcesInside3 = Queue(maxsize=1000)
threeDimensionalForcesInside4 = Queue(maxsize=1000)
threeDimensionalForcesOutside1 = Queue(maxsize=1000)
threeDimensionalForcesOutside2 = Queue(maxsize=1000)
threeDimensionalForcesOutside3 = Queue(maxsize=1000)
threeDimensionalForcesOutside4 = Queue(maxsize=1000)
displayData_lock = Lock()


class DisplayDataParseThread(Thread):
    def __init__(self):
        self.packPos = 0
        self.packBuf = [0]*30
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
        global mutualCapacitanceQueue, threeDimensionalForcesInside1, threeDimensionalForcesInside2, threeDimensionalForcesInside3, threeDimensionalForcesInside4  
        global threeDimensionalForcesOutside1, threeDimensionalForcesOutside2, threeDimensionalForcesOutside3, threeDimensionalForcesOutside4
        
        readLen = 0
        while GUI.quitApplication == 0:
            n = UartReceiveThread.displayDataReceiveBuffer.qsize()
            readLen = 0
            if n >= 4:
                for i in range(4):
                    UartReceiveThread.displayDataBuffer_lock.acquire()
                    data = UartReceiveThread.displayDataReceiveBuffer.get()
                    UartReceiveThread.displayDataBuffer_lock.release()
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
                    elif data == 0x09 and self.packPos == 3:
                        self.packBuf[self.packPos] = data
                        self.packPos += 1
                        if data == 0x09:
                            len = 24
                            readLen = 20
                    
            if readLen > 0:
                n = UartReceiveThread.displayDataReceiveBuffer.qsize()
                while n < readLen:
                    sleep(0.001)
                    n = UartReceiveThread.displayDataReceiveBuffer.qsize()

                if n >= readLen:
                    for i in range(readLen):
                        UartReceiveThread.displayDataBuffer_lock.acquire()
                        data = UartReceiveThread.displayDataReceiveBuffer.get()
                        UartReceiveThread.displayDataBuffer_lock.release()
                        if len > 0 and self.packPos < len:
                            self.packBuf[self.packPos] = data
                            self.packPos += 1
                            if len == self.packPos:
                                self.packPos = 0
                                checksum = self.getCheckSum(self.packBuf, len - 2)
                                
                                if checksum == (self.packBuf[len - 1] * 256) + self.packBuf[len - 2]:
                                    displayData_lock.acquire()
                                    mutualCapacitanceQueue.put(self.packBuf[4] + self.packBuf[5])
                                    threeDimensionalForcesInside1.put(self.packBuf[6] + (self.packBuf[7] * 256))
                                    threeDimensionalForcesInside2.put(self.packBuf[8] + (self.packBuf[9] * 256))
                                    threeDimensionalForcesInside3.put(self.packBuf[10] + (self.packBuf[11] * 256))
                                    threeDimensionalForcesInside4.put(self.packBuf[12] + (self.packBuf[13] * 256))
                                    threeDimensionalForcesOutside1.put(self.packBuf[14] + (self.packBuf[15] * 256))
                                    threeDimensionalForcesOutside2.put(self.packBuf[16] + (self.packBuf[17] * 256))
                                    threeDimensionalForcesOutside3.put(self.packBuf[18] + (self.packBuf[19] * 256))
                                    threeDimensionalForcesOutside4.put(self.packBuf[20] + (self.packBuf[21] * 256))
                                    displayData_lock.release()

                                    strbuf = "--- receiveMessageQueue --- " + str(mutualCapacitanceQueue.qsize())
                                    Utility.formatPrinting(strbuf)
                                else:
                                    print("displayData checksum error")
                        else:
                            self.packBuf = [0] * 30
                            self.packPos = 0
                            print("self.packBuf = [0]*30 ")

            sleep(0.01)
        print("DisplayDataParseThread quit")
