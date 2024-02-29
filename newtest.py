import GUI
import UartReceiveThread
import URRobotThread
import UartProtocolParseThread, displayDataParseThread, collisionParseThread
import UartSendThread, snnDataWriteToExcel
import TransformCoordinateThread
import sys

if __name__ == "__main__":

    URRobot_Thread = URRobotThread.URRobotThread()
    URRobot_Thread.start()

    UartProtocolParse_Thread = UartProtocolParseThread.UartProtocolParseThread()
    UartProtocolParse_Thread.start()

    UartReceive_Thread = UartReceiveThread.UartReceiveThread()
    UartReceive_Thread.start()

    UartSend_Thread = UartSendThread.UartSendThread()
    UartSend_Thread.start()

    displayDataParseThread.DisplayDataParseThread()
    TransformCoordinateThread.TransformCoordThread()
    collisionParseThread.CollisionParseThread()
    snnDataWriteToExcel.SnnDataWriteToExcel()

    app = GUI.main()

    sys.exit()