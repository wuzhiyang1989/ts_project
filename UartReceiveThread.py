import serial
import serial.tools.list_ports
import Utility, GUI
from queue import Queue
from threading import Thread, Lock
from time import sleep

dataReceiveBuffer = Queue(maxsize=10000)
displayDataReceiveBuffer = Queue(maxsize=10000)
ReceiveBuffer_lock = Lock()
collisionDataBuffer = Queue(maxsize=10000)
collisionDataBuffer_lock = Lock()

serialPort = []
port_list = list(serial.tools.list_ports.comports())
if len(port_list) == 0:
    print('无可用串口，不能开始')
for port in port_list:
    print(port[0])
    serialPort.append(port[0])
ser = serial.Serial(serialPort[0], 9600, timeout=0.5)
uart = serial.Serial(serialPort[1], 256000, timeout=0.5)

class UartReceiveThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.packPos = 0
        self.packBuf = [0]*30
        self.pack_buf = []

    def getCheckSum(self, buf, len):
        sum = 0
        for i in range(len):
            sum += buf[i]
        return sum & 0xFF

    def run(self):
        getLen = 0

        while GUI.quitApplication == 0:
            data_ = ser.read_all()
            m = len(data_)

            strbuffer = " ****** ReceiveThread ******  " + str(data_.hex())
            if m > 0:
                Utility.formatPrinting(strbuffer)

            for i in range(m):
                self.pack_buf.append(data_[i])
                        
            while len(self.pack_buf) >= 16:
                if self.pack_buf[0] == 0x55 and self.pack_buf[1] == 0xAA and self.pack_buf[2] == 0x05 and self.pack_buf[3] == 0xE4 and self.pack_buf[6] == 0x08:
                    checksum = self.getCheckSum(self.pack_buf, 15)
                    if checksum == self.pack_buf[15]:
                        collisionDataBuffer_lock.acquire()
                        for i in range(16):
                            collisionDataBuffer.put(self.pack_buf[i])
                        collisionDataBuffer_lock.release()
                    else:
                        print("collisionDataBuffer overflow ! ")
                    del self.pack_buf[0:16]
                else:
                    del self.pack_buf[0]
                    print("packBuf error ")
            
            data = uart.read_all()
            n = len(data)

            if n > 0:				
                strbuf = "--- ReceiveThread --- " + str(data.hex())
                # Utility.formatPrinting(strbuf)
                ReceiveBuffer_lock.acquire()
                for i in range(n):
                    if data[i] == 0x55 and self.packPos == 0:
                        getLen = 0
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                    elif data[i] == 0xAA and self.packPos == 1:
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                    elif data[i] == 0x01 and self.packPos == 2:
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                    elif data[i] == 0x03 and self.packPos == 2:
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                    elif data[i] == 0x09 and self.packPos == 3:
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                        getLen = 24
                    elif (data[i] == 0xE1 or data[i] == 0xE2 or data[i] == 0xE3 or data[i] == 0xE4) and self.packPos == 3:
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                        getLen = 8 if data[i] == 0xE1 else 10
                    elif getLen > 0 and self.packPos < getLen:
                        self.packBuf[self.packPos] = data[i]
                        self.packPos += 1
                        if getLen == self.packPos:
                            for i in range(getLen):
                                if getLen == 24:
                                    if displayDataReceiveBuffer.qsize() < displayDataReceiveBuffer.maxsize:
                                        displayDataReceiveBuffer.put(self.packBuf[i])             
                                else:
                                    if dataReceiveBuffer.qsize() < dataReceiveBuffer.maxsize:
                                        dataReceiveBuffer.put(self.packBuf[i]) 

                            self.packPos = 0 
                            self.packBuf = [0] * 30
                    else :
                        print("dataReceiveBuffer overflow !")
                ReceiveBuffer_lock.release()

            sleep(0.001)

        ser.close()
        uart.close()
        print("UartReceiveThread quit")
      