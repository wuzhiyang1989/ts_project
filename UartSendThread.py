import Utility, GUI
import UartReceiveThread
from threading import Thread
from time import sleep

class UartSendThread(Thread):
    def __init__(self):
        self.sendcount = 0
        Thread.__init__(self)

    def getCheckSum(self, buf, len):
        sum = 0
        for i in range(len):
            sum += buf[i]
        return sum & 0xFF

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
                elif cmd == "StartGrab":
                    data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0x02, 0xE9]
                elif cmd == "MoveComplete":
                    data = [0x55, 0xAA, 0x04, 0xE3, 0x00, 0x00, 0x02, 0x00, 0x0F, 0xF7]
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
                data[4] = (self.sendcount & 0xFF00) >> 8
                data[5] = self.sendcount & 0x00FF
                data[len - 1] = self.getCheckSum(data, len - 1)
                UartReceiveThread.uart.write(data)
                strbuf = " << SendThread >> " + cmd
                Utility.formatPrinting(strbuf)
                self.sendcount += 1
                if self.sendcount == 0x10000:
                    self.sendcount = 0
            sleep(0.001)

        print("UartSendThread quit")
       