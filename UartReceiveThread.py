import serial
import serial.tools.list_ports
import Utility, GUI
from queue import Queue
from threading import Thread, Lock
from time import sleep

dataReceiveBuffer = Queue(maxsize=10000)
ReceiveBuffer_lock = Lock()
displayDataReceiveBuffer = Queue(maxsize=10000)
displayDataBuffer_lock = Lock()

port_list = list(serial.tools.list_ports.comports())
if len(port_list) == 0:
    print('无可用串口，不能开始')
for port in port_list:
    print(port[0])
    serialPort = port[0]
uart = serial.Serial(serialPort, 256000, timeout=0.5)

class UartReceiveThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.packPos = 0

    def run(self):
        getLen = 0
        while GUI.quitApplication == 0:
            data = uart.read_all()
            n = len(data)

            if n > 0 and (n==8 or n==10):				
                strbuf = "------ReceiveThread------ " + str(data)
                Utility.formatPrinting(strbuf)

                ReceiveBuffer_lock.acquire()
                for i in range(n):
                    if dataReceiveBuffer.qsize() < dataReceiveBuffer.maxsize:
                        if data[i] == 0x55 and self.packPos == 0:
                            getLen = 0
                            dataReceiveBuffer.put(data[i])
                            self.packPos += 1
                        elif data[i] == 0xAA and self.packPos == 1:
                            dataReceiveBuffer.put(data[i])
                            self.packPos += 1
                        elif data[i] == 0x03 and self.packPos == 2:
                            dataReceiveBuffer.put(data[i])
                            self.packPos += 1
                        elif (data[i] == 0xE1 or data[i] == 0xE2 or data[i] == 0xE3 or data[i] == 0xE4) and self.packPos == 3:
                            dataReceiveBuffer.put(data[i])
                            self.packPos += 1
                            getLen = 8 if data[i] == 0xE1 else 10
                        elif getLen > 0 and self.packPos < getLen:
                            dataReceiveBuffer.put(data[i])
                            self.packPos += 1
                            if getLen == self.packPos:
                                self.packPos = 0          
                    else :
                        print("dataReceiveBuffer overflow !")
                ReceiveBuffer_lock.release()

            elif n > 0 and n == 24:	
                strbuf = "------ReceiveThread------ " + str(data)
                # Utility.formatPrinting(strbuf)

                displayDataBuffer_lock.acquire()
                for i in range(n):
                    if displayDataReceiveBuffer.qsize() < displayDataReceiveBuffer.maxsize:
                        if data[i] == 0x55 and self.packPos == 0:
                            getLen = 0
                            displayDataReceiveBuffer.put(data[i])
                            self.packPos += 1
                        elif data[i] == 0xAA and self.packPos == 1:
                            displayDataReceiveBuffer.put(data[i])
                            self.packPos += 1
                        elif data[i] == 0x01 and self.packPos == 2:
                            displayDataReceiveBuffer.put(data[i])
                            self.packPos += 1
                        elif data[i] == 0x09 and self.packPos == 3:
                            displayDataReceiveBuffer.put(data[i])
                            self.packPos += 1
                            getLen = 24
                        elif getLen > 0 and self.packPos < getLen:
                            displayDataReceiveBuffer.put(data[i])
                            self.packPos += 1
                            if getLen == self.packPos:
                                self.packPos = 0          
                    else :
                        print("displayDataReceiveBuffer overflow !")
                displayDataBuffer_lock.release()
                
            sleep(0.001)

        uart.close()
        print("UartReceiveThread quit")
      