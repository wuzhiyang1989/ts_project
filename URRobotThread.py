import urx
import GUI, Utility, UartReceiveThread
import UartProtocolParseThread, collisionParseThread
import TransformCoordinateThread, UartSendThread
import numpy as np

from time import sleep, time
from threading import Thread

stateMachine = ""
task_num = 0
task_sub_step = 0

class URRobotThread(Thread):
    def __init__(self):
        print("URRobotThread.__init__")
        Thread.__init__(self)
        self.send = [0]*6
        self.receive = [0]*6
        self.waitTime = 0
        self.receiveLift = 0
        self.receiveHand = 0
        self.rob = urx.Robot("192.168.1.100")
        self.sendcount_ = 0
        self.sendcount = 0
        self.coll = collisionParseThread.CollisionParseThread()
        self.uartParse = UartProtocolParseThread.UartProtocolParseThread()
        self.sendMessage = UartSendThread.UartSendThread()

    def send_collisionMessage(self):
        data_ = [0x55, 0xAA, 0x06, 0xE4, 0x00, 0x00, 0x00, 0xE9]
        len_ = 8
        data_[4] = (self.sendcount_ & 0xFF00) >> 8
        data_[5] = self.sendcount_ & 0x00FF
        data_[len_ - 1] = self.coll.getCheckSum(data_, len_ - 1)

        UartReceiveThread.ser.write(data_)
        strbuf = " << Send >> reply_CollisionMessage" 
        Utility.formatPrinting(strbuf)
        self.sendcount_ += 1
        if self.sendcount_ == 0x10000:
            self.sendcount_ = 0
    
    def send_gripperStopMessage(self, collisionState):
        if collisionState == "downSend_CollisionStop":
            data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0xF0, 0xE9]
            len = 10
            data[4] = (self.sendcount & 0xFF00) >> 8
            data[5] = self.sendcount & 0x00FF
            data[len - 1] = self.uartParse.getCheckSum(data, len - 1)

            self.sendMessage.sendSplitData(data, len)
            strbuf = " << Send >> gripperStopMessage" + str(data) 
            Utility.formatPrinting(strbuf)
           
        if collisionState == "downSend_NormalMove":
            data = [0x55, 0xAA, 0x04, 0xE2, 0x00, 0x00, 0x02, 0x00, 0xEF, 0xE9]
            len = 10
            data[4] = (self.sendcount & 0xFF00) >> 8
            data[5] = self.sendcount & 0x00FF
            data[len - 1] = self.uartParse.getCheckSum(data, len - 1)

            self.sendMessage.sendSplitData(data, len)
            strbuf = " << Send >> gripperRenewMessage" + str(data) 
            Utility.formatPrinting(strbuf)

        self.sendcount += 1
        if self.sendcount == 0x10000:
            self.sendcount = 0
                
    def run(self):
        print("URRobotThread.run")
        global stateMachine, task_num, task_sub_step, task_num_collision, task_sub_collision

        task_list = [
            ["wait_start_btn", "move_z", "move_y", "move_x", "send_message", "wait_message","move_z", "send_message",
             "wait_message", "task_end"],

            # 任务1，将物品移动到定点的位置
            # ["move_x", "move_y","send_message", "wait_message", "send_message", "wait_message", "move_z", "send_message",
            #  "move_y", "move_x", "move_y", "wait_message", "send_message", "wait_message", "move_z", "send_message", 
            #  "wait_message", "move_y", "move_x", "task_end"],

            # 任务1，将物品抓起再放下
            ["move_x", "move_y","send_message", "wait_message", "send_message", "wait_message", "move_z", "send_message",
             "wait_message", "send_message", "wait_message", "move_z", "send_message", "wait_message", "move_y", "move_x", 
             "task_end"],

            # ["move_x", "move_y", "send_message", "wait_message", "move_x", "move_y", "send_message", "wait_message",
            #  "send_message", "wait_message", "task_end"],
            ["move_x", "move_y", "send_message", "wait_message", "send_message", "wait_message", "send_message", "wait_message",
              "move_x", "move_y", "task_end"],

            ["move_y", "send_message", "wait_message", "move_z", "send_message", "wait_message", "move_x", "task_end"]]

        message_list = [
            ["", "", "", "", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete", ""],

            # 任务1，将物品移动到定点的位置
            # ["", "", "StartPrepare", "downSend_PrepareComplete", "StartGrab", "downSend_GrabComplete", "", "LiftComplete", "", 
            #  "", "", "downSend_RequestDecline", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete",
            #  "", "", ""],

            # 任务1，将物品抓起再放下
            ["", "", "StartPrepare", "downSend_PrepareComplete", "StartGrab", "downSend_GrabComplete", "", "LiftComplete", 
             "downSend_RequestDecline", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete",
             "", "", ""],

            # ["", "", "HandInteraction", "downSend_RequestDecline", "", "", "StartDecline", "downReply_StartDecline",
            #  "CompleteDecline", "downSend_TaskComplete",""],
            ["", "", "HandInteraction", "downSend_RequestDecline", "StartDecline", "downReply_StartDecline",  
             "CompleteDecline", "downSend_TaskComplete", "", "", ""],

            ["", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete", "", ""]]

        position_list = [
            [[0, 0, 0, 0, 0, 0], [0, 0, 0.275, 0, 0, 0], [0, -0.268, 0, 0, 0, 0], [-0.107, 0, 0, 0.046, 2.200, -2.253],
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.106, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],

            # 任务1，将物品移动到定点的位置
            # [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
            #  [0, 0, 0.275, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, -0.268, 0, 0, 0, 0], [-0.386, 0, 0, 0, 0, 0], [0, -0.496, 0, 0, 0, 0],
            #  [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.106, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
            #  [0, -0.268, 0, 0, 0, 0], [-0.107, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],

            # 任务1，将物品抓起再放下
            [[0, 0, 0, 0.046, 2.200, -2.253], [0, 0, 0, 0, 0, 0],[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
             [0, 0, 0.275, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.106, 0, 0, 0], 
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, -0.268, 0, 0, 0, 0], [-0.107, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],

            # [[-0.156, 0, 0, 0, 0, 0], [0, -0.566, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [-0.156, 0, 0, 0, 0, 0], [0, -0.268, 0, 0, 0, 0],
            #  [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],
            [[-0.156, 0, 0, 0, 0, 0], [0, -0.566, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [-0.156, 0, 0, 0, 0, 0], [0, -0.268, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],


            [[0, -0.268, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.106, 0, 0, 0], [0, 0, 0, 0, 0, 0],
             [-0.107, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]]
        
        hand_x_left_limit = -0.236
        hand_x_right_limit = -0.076

        x_left_limit = -0.016         # -0.410
        x_right_limit = 0.426         # 0.436
        y_end_limit = -0.696          # -0.690
        y_front_limit = -0.366        # -0.268
    
        xmin = -0.370
        xmax = 0.436
        ymin = -0.720
        ymax = -0.260
        zmin = 0.100
        zmax = 0.560

        task_num_collision = 0
        task_sub_collision = 0
        
        a = 0.1  
        v0 = 0.05
        v1 = 0.08
        v2 = 0.2
        direction = 0
        zMoveDirection = 0

        lastmoveSource = 0
        moveSource = 0
        enableMove = 0
        pointcloud2 = np.array([-0.107, -0.568, 0.106])
        flag_pointcloud = False
        
        GUI.stateMachine_Lock.acquire()
        stateMachine = task_list[task_num][task_sub_step]
        GUI.stateMachine_Lock.release()
        
        current_point = self.rob.getl()
        target_point = [current_point[0],current_point[1],current_point[2],current_point[3],current_point[4],current_point[5]]
        source_point = [current_point[0],current_point[1],current_point[2],current_point[3],current_point[4],current_point[5]]

        while GUI.quitApplication == 0:
            GUI.stateMachine_Lock.acquire()
            status = stateMachine
            GUI.stateMachine_Lock.release()

            TransformCoordinateThread.pointCloud_lock.acquire()
            pointcloud2[0] = TransformCoordinateThread.pointcloud[0]
            pointcloud2[1] = TransformCoordinateThread.pointcloud[1]
            pointcloud2[2] = TransformCoordinateThread.pointcloud[2]
            # y坐标计算得出是一个正值，与机械臂运动方向相反，在这里做了取反操作，和减去夹爪的长度
            # pointcloud2[1] = -(pointcloud2[1] - 0.19)
            TransformCoordinateThread.pointCloud_lock.release()
                      
            if not np.isnan(pointcloud2).any() and x_left_limit < pointcloud2[0] < x_right_limit and y_end_limit < pointcloud2[1] < y_front_limit:
                flag_pointcloud = True
            else:
                flag_pointcloud = False

            this_message = ""
            UartProtocolParseThread.receiveMessageQueue_lock.acquire()
            if not UartProtocolParseThread.receiveMessageQueue.empty():
                this_message = UartProtocolParseThread.receiveMessageQueue.get()
            UartProtocolParseThread.receiveMessageQueue_lock.release()

            collision_message = ""
            collisionParseThread.collisionMessageQueue_lock.acquire()
            if not collisionParseThread.collisionMessageQueue.empty():
                collision_message = collisionParseThread.collisionMessageQueue.get()
            collisionParseThread.collisionMessageQueue_lock.release()

            if collision_message == "downSend_CollisionStop":
                Utility.formatPrinting("wait_message << downSend_CollisionStop")
                self.rob.stopl(acc=0.8)
                # 在夹爪开始抓取——抓取结束的过程中，向主控发送停止命令
                if (task_num == 1 and task_sub_step == 4) or (task_num == 1 and task_sub_step == 5):
                    self.send_gripperStopMessage(collision_message)
                
                task_num_collision = task_num
                task_sub_collision = task_sub_step
                self.send_collisionMessage()  
                
            elif collision_message == "downSend_NormalMove":
                Utility.formatPrinting("wait_message << downSend_NormalMove")
                # 在夹爪开始抓取——抓取结束的过程中，向主控发送恢复运行命令
                if (task_num == 1 and task_sub_step == 4) or (task_num == 1 and task_sub_step == 5):
                    self.send_gripperStopMessage(collision_message)
                self.send_collisionMessage()
                if task_num_collision == 0 and task_sub_collision == 0:
                    pass
                else:
                    status = task_list[task_num_collision][task_sub_collision]
                    task_num = task_num_collision
                    task_sub_step = task_sub_collision
                             
            if this_message == "downSend_FallDown":
                if task_num == 1 or task_num == 2:
                    self.rob.stopl(acc=a)
                    if UartProtocolParseThread.someThing == 1:
                        GUI.displayPictureName = "Dropped"
                    task_num_break = task_num
                    task_num = 3             # 如果滑落，执行任务3
                    task_sub_step = 0
                    status = task_list[task_num][task_sub_step]
                    Utility.formatPrinting("wait_message << downSend_FallDown_0")

            if this_message == "downSend_Plastic":
                GUI.displayPictureName = "Plastic"
                Utility.formatPrinting("wait_message << downSend_Plastic")
            elif this_message == "downSend_Wood":
                GUI.displayPictureName = "Wood"
                Utility.formatPrinting("wait_message << downSend_Wood")
            elif this_message == "downSend_Sponge":
                GUI.displayPictureName = "Sponge"
                Utility.formatPrinting("wait_message << downSend_Sponge")
            elif this_message == "downSend_Glass":
                GUI.displayPictureName = "Glass"
                Utility.formatPrinting("wait_message << downSend_Glass")

            if status == "move_z":
                current_point = self.rob.getl()
                target_point = [current_point[0],current_point[1],current_point[2],current_point[3],current_point[4],current_point[5]]
                target_point[2] = position_list[task_num][task_sub_step][2]  # z change var
                
                if target_point[2] > current_point[2]:  # lift
                    v = 0.03 # v0                       # slow lift
                    zMoveDirection = 1
                    a = 0.1
                    source_point = current_point
                else:
                    a = 0.05
                    v = v1                              # fast down
                    zMoveDirection = -1

                if not np.isnan(target_point).any() and zmin < target_point[2] < zmax:
                    self.rob.movel(target_point, acc=a, vel=v, wait=False)
                    status = "wait_move_z"
                else:
                    Utility.formatPrinting(str(target_point[2]) + " Z coordinate overstep the boundary!")
                    self.rob.stopl(acc = a)
                    # task_num = 3             # 如果坐标越界，执行任务3 (回原点)
                    # task_sub_step = 0
                    # status = task_list[task_num][task_sub_step]
                    status = "task_end"
                
            elif status == "wait_move_z":
                current_point = self.rob.getl()
                if zMoveDirection == 1:                             # lift
                    if current_point[2] - source_point[2] > 0.03:   # lift 2 cm
                        zMoveDirection = 0
                        self.rob.movel(target_point, acc=a, vel=v1, wait=False) # fast lift
                if abs(current_point[2] - target_point[2]) < 0.001:
                    task_sub_step += 1
                    status = task_list[task_num][task_sub_step]
                    a = 0.05
                             
            elif status == "change_pose":
                current_point = self.rob.getl()
                target_point = current_point
                target_point[2] = 0.106
                target_point[3] = position_list[task_num][task_sub_step][3]
                target_point[4] = position_list[task_num][task_sub_step][4]
                target_point[5] = position_list[task_num][task_sub_step][5]
                
                self.rob.movel(target_point, acc=a, vel=v1, wait=False)
                status = "wait_change_pose"

            elif status == "wait_change_pose":
                current_point = self.rob.getl()
                if abs(current_point[3] - target_point[3]) < 0.001 and abs(current_point[4] - target_point[4]) < 0.001 and abs(current_point[5] - target_point[5]) < 0.001:
                    task_sub_step += 1
                    status = task_list[task_num][task_sub_step]
            
            elif status == "move_x":
                current_point = self.rob.getl()
                target_point = current_point
                target_point[0] = position_list[task_num][task_sub_step][0]  # x change var

                ##################################################################
                if (task_num == 1 and task_sub_step == 0) or (task_num == 0 and task_sub_step == 3):            # change pose
                    target_point[3] = position_list[task_num][task_sub_step][3]
                    target_point[4] = position_list[task_num][task_sub_step][4]
                    target_point[5] = position_list[task_num][task_sub_step][5]
                ##################################################################

                if task_num == 1 and task_sub_step == 0:
                    target_point[0] = pointcloud2[0]
                    
                if not np.isnan(target_point).any() and xmin < target_point[0] < xmax:
                    self.rob.movel(target_point, acc=a, vel=v2, wait=False)
                    status = "wait_move_x"
                else:
                    Utility.formatPrinting(str(target_point[0]) + " X coordinate overstep the boundary!")
                    self.rob.stopl(acc = a)
                    # task_num = 3             # 如果坐标越界，执行任务3 (回原点)
                    # task_sub_step = 0
                    # status = task_list[task_num][task_sub_step]
                    status = "task_end"
                
            elif status == "wait_move_x":
                current_point = self.rob.getl()
                # 判断移动目标值是否到达指定位置
                if abs(current_point[0] - target_point[0]) < 0.005:
                    task_sub_step += 1  
                    status = task_list[task_num][task_sub_step]  
                # 判断没有抓取任务，保持人手互动任务    
                if task_num == 2 and flag_pointcloud == False and task_sub_step == 9:
                    # task_sub_step = 2
                    status = task_list[task_num][task_sub_step]   
        
            elif status == "move_y":
                current_point = self.rob.getl()
                target_point = current_point
                target_point[1] = position_list[task_num][task_sub_step][1]  

                if task_num == 1 and task_sub_step == 1:
                    target_point[1] = pointcloud2[1]
                    
                if not np.isnan(target_point).any() and ymin < target_point[1] < ymax:
                    self.rob.movel(target_point, acc=a, vel=v2, wait=False)
                    status = "wait_move_y"
                else:
                    Utility.formatPrinting(str(target_point[1]) + " Y coordinate overstep the boundary!")
                    self.rob.stopl(acc = a)
                    # task_num = 3             # 如果坐标越界，执行任务3 (回原点)
                    # task_sub_step = 0
                    # status = task_list[task_num][task_sub_step]
                    status = "task_end"

            elif status == "wait_move_y":
                current_point = self.rob.getl()
                if abs(current_point[1] - target_point[1]) < 0.005:
                    task_sub_step += 1
                    status = task_list[task_num][task_sub_step]

            elif status == "wait_start_btn":
                if GUI.runState == 1:
                    current_point = self.rob.getl()
                    task_sub_step += 1
                    status = task_list[task_num][task_sub_step]
                    
            elif status == "UI_Stop":
                self.rob.stopl(acc = a)
                task_num = 0
                task_sub_step = 0
                status = task_list[task_num][task_sub_step]
                current_point = self.rob.getl()
                Utility.formatPrinting(status)

            elif status == "send_message":
                GUI.send_lock.acquire()
                GUI.sendMessageQueue.put(message_list[task_num][task_sub_step])
                if (message_list[task_num][task_sub_step] == "StartPrepare"):
                    self.send[0] = 1
                elif (message_list[task_num][task_sub_step] == "StartGrab"):
                    self.send[1] = 1
                elif (message_list[task_num][task_sub_step] == "LiftComplete"):
                    self.send[2] = 1
                elif (message_list[task_num][task_sub_step] == "StartDecline"):
                    self.send[3] = 1
                elif (message_list[task_num][task_sub_step] == "CompleteDecline"):
                    self.send[4] = 1
                elif (message_list[task_num][task_sub_step] == "HandInteraction"):
                    self.send[5] = 1
                GUI.send_lock.release()
                
                task_sub_step += 1
                status = task_list[task_num][task_sub_step]

            elif status == "wait_message":

                if task_num == 2:
                    UartProtocolParseThread.moveSourceLock.acquire()
                    moveSource = UartProtocolParseThread.moveSource
                    UartProtocolParseThread.moveSource = 0
                    UartProtocolParseThread.moveSourceLock.release()
		                
                    current_point = self.rob.getl()
                    # Utility.formatPrinting(" lastmoveSource : " + str(lastmoveSource) + " moveSource : " + str(moveSource) + " enableMove: " + str(enableMove) + "  current_point[1] : " + str(current_point[1]))
		                
                    if lastmoveSource == 0 or lastmoveSource == 2:
                        enableMove = 1
                    else:
                        if moveSource == 1:
                            enableMove = 1
                        else:
                            enableMove = 0
                        current_point = self.rob.getl()
                        if direction == 1:
                            if abs(current_point[0] - hand_x_right_limit) < 0.001:
                                moveSource = 0
                        if direction == -1:
                            if abs(current_point[0] - hand_x_left_limit) < 0.001:
                                moveSource = 0

                    if lastmoveSource != moveSource:
                        lastmoveSource = moveSource  

                if self.send[0] == 1:
                    if self.waitTime == 0:
                        self.waitTime = 1
                        t = time()
                    elif self.waitTime == 1 and abs(time() - t) > 0.5:
                        if self.receive[0] == 0:
                            task_num = 1
                            task_sub_step = 2
                            status = task_list[task_num][task_sub_step] 
                            self.waitTime = 0
                        else:
                            self.send[0] = 0
                            self.receive[0] = 0
                            self.waitTime = 0
                
                elif self.send[1] == 1:
                    if self.waitTime == 0:
                        self.waitTime = 1
                        t = time()
                    elif self.waitTime == 1 and abs(time() - t) > 0.5:
                        if self.receive[1] == 0:
                            task_num = 1
                            task_sub_step = 4
                            status = task_list[task_num][task_sub_step] 
                            self.waitTime = 0
                        else:
                            self.send[1] = 0
                            self.receive[1] = 0
                            self.waitTime = 0

                elif self.send[2] == 1:
                    if self.waitTime == 0:
                        self.waitTime = 1
                        t = time()
                    elif self.waitTime == 1 and abs(time() - t) > 0.5:
                        if self.receive[2] == 0:
                            task_num = 1
                            task_sub_step = 7
                            status = task_list[task_num][task_sub_step] 
                            self.waitTime = 0
                        else:
                            self.send[2] = 0
                            self.receive[2] = 0
                            self.waitTime = 0
                
                elif self.send[3] == 1:
                    if self.waitTime == 0:
                        self.waitTime = 1
                        t = time()
                    elif self.waitTime == 1 and abs(time() - t) > 0.5:
                        if self.receive[3] == 0:
                            if task_num == 0:
                                task_sub_step = 4    
                            elif task_num == 1:
                                task_sub_step = 9
                            elif task_num == 2:
                                task_sub_step = 4
                            elif task_num == 3:
                                task_sub_step = 1
                            status = task_list[task_num][task_sub_step] 
                            self.waitTime = 0
                        else:
                            self.send[3] = 0
                            self.receive[3] = 0
                            self.waitTime = 0

                elif self.send[4] == 1:
                    if self.waitTime == 0:
                        self.waitTime = 1
                        t = time()
                    elif self.waitTime == 1 and abs(time() - t) > 0.5:
                        if self.receive[4] == 0:
                            if task_num == 0:
                                task_sub_step = 7  
                            elif task_num == 1:
                                task_sub_step = 12
                            elif task_num == 2:
                                task_sub_step = 6
                            elif task_num == 3:
                                task_sub_step = 4
                            status = task_list[task_num][task_sub_step] 
                            self.waitTime = 0
                        else:
                            self.send[4] = 0
                            self.receive[4] = 0
                            self.waitTime = 0
                            
                elif self.send[5] == 1:
                    if self.waitTime == 0:
                        self.waitTime = 1
                        t = time()
                    elif self.waitTime == 1 and abs(time() - t) > 0.5:
                        if self.receive[5] == 0:
                            task_num = 2
                            task_sub_step = 2
                            status = task_list[task_num][task_sub_step] 
                            self.waitTime = 0
                        else:
                            self.send[5] = 0
                            self.receive[5] = 0
                            self.waitTime = 0      
                
                if this_message == message_list[task_num][task_sub_step]:
                    Utility.formatPrinting("wait_message << " + message_list[task_num][task_sub_step])
                    task_sub_step += 1
                    status = task_list[task_num][task_sub_step]
                    if this_message == "downSend_GrabComplete":
                        GUI.send_lock.acquire()
                        GUI.sendMessageQueue.put("upReply_GrabComplete")
                        GUI.send_lock.release()
                        GUI.displayPictureName = "Stable"
                    elif this_message == "downReply_StartDecline":
                        self.receive[3] = 1
                        Utility.formatPrinting(str(self.receive[3]))
                    elif this_message == "downSend_RequestDecline":
                        if self.receiveLift == 1:
                            task_num = 1
                            task_sub_step = 9
                        elif self.receiveHand == 1:
                            task_num = 2
                            task_sub_step = 4
                        else:
                            if task_num == 1:
                                task_sub_step = 7
                            elif task_num == 2:
                                task_sub_step == 2
                            
                            self.receiveLift = 0
                            self.receiveHand = 0
                        status = task_list[task_num][task_sub_step]

                elif this_message == "downReply_StartPrepare":
                    self.receive[0] = 1
                    Utility.formatPrinting("wait_message << downReply_StartPrepare " + str(self.receive[0]))
                elif this_message == "downSend_PrepareGrabDemo":
                    Utility.formatPrinting("wait_message << downSend_PrepareGrabDemo")
                elif this_message == "downSend_PrepareComplete":
                    GUI.displayPictureName = "Nothing"
                    Utility.formatPrinting("wait_message << downSend_PrepareComplete")
                elif this_message == "downReply_StartGrab":
                    self.receive[1] = 1
                    GUI.displayPictureName = "Grabbing"
                    Utility.formatPrinting("wait_message << downReply_StartGrab " + str(self.receive[1]))
                elif this_message == "downSend_GripperState":
                    if UartProtocolParseThread.someThing == 1:  # gripperDistance
                        GUI.displayPictureName = "Something"
                    else:  # gripperDistance
                        GUI.displayPictureName = "Nothing"
                    Utility.formatPrinting("wait_message << downSend_GripperState")
                elif this_message == "downSend_Shrink":
                    #GUI.displayPictureName = "Stable"
                    Utility.formatPrinting("wait_message << downSend_Shrink")
                elif this_message == "downSend_Stable":
                    #GUI.displayPictureName = "Stable"
                    Utility.formatPrinting("wait_message << downSend_Stable")
                elif this_message == "downSend_loosen":
                    #GUI.displayPictureName = "Stable"
                    Utility.formatPrinting("wait_message << downSend_loosen")
                elif this_message == "downSend_FallDown":
                    Utility.formatPrinting("wait_message << downSend_FallDown_1")
                elif this_message == "downReply_LiftComplete":
                    self.receive[2] = 1
                    self.receiveLift = 1
                    Utility.formatPrinting("wait_message << downReply_LiftComplete " + str(self.receive[2]))
                elif this_message == "downReply_CompleteDecline":
                    self.receive[4] = 1
                    Utility.formatPrinting("wait_message << downReply_CompleteDecline " + str(self.receive[4]))
                elif this_message == "downSend_GripperOpenComplete":
                    Utility.formatPrinting("wait_message << downSend_GripperOpenComplete")
                # 没有物品时的任务结束
                elif this_message == "downSend_TaskComplete":   # exception complete
                    if task_num == 1:
                        task_sub_step = 14
                        status = task_list[task_num][task_sub_step]
                elif this_message == "downReply_UIStop":
                    Utility.formatPrinting("wait_message << downReply_UIStop")
                elif this_message == "downReply_HandInteraction":
                    self.receive[5] = 1
                    self.receiveHand = 1
                    Utility.formatPrinting("wait_message << downReply_HandInteraction " + str(self.receive[5]))
                elif this_message == "downReply_MutualCapacitanceClean":
                    Utility.formatPrinting("wait_message << downReply_MutualCapacitanceClean")
                
                elif this_message == "downSend_MoveLeft":
                    if (task_num == 1 and task_sub_step == 3) or (task_num == 1 and task_sub_step == 5):
                        current_point = self.rob.getl()
                        target_point = current_point
                        target_point[0] -= 0.002
                        self.rob.movel(target_point, acc=a, vel=v0, wait=False)
                        timestamp = time()
                        Utility.formatPrinting("wait_message << downSend_MoveLeft :: target " + stateMachine + " >> " + " ".join(map(str,target_point)))
                        
                        while GUI.quitApplication == 0:
                            current_point = self.rob.getl()
                            now = time()
                            if (current_point[0] - target_point[0] <= 0.0001) or (now - timestamp) <= 1:
                                GUI.send_lock.acquire()
                                GUI.sendMessageQueue.put("MoveComplete")
                                GUI.send_lock.release()
                                break

                    if task_num == 2 and enableMove == 1:
                        if direction != -1:
                            direction = -1 
                            current_point = self.rob.getl()
                            target_point = current_point
                            target_point[0] = hand_x_left_limit
                            self.rob.movel(target_point, acc=a, vel=0.03, wait=False)
                            Utility.formatPrinting("wait_message << downSend_MoveLeft :: target " + stateMachine + " >> " + " ".join(map(str,target_point)))

                elif this_message == "downSend_MoveRight":
                    if (task_num == 1 and task_sub_step == 3) or (task_num == 1 and task_sub_step == 5):
                        current_point = self.rob.getl()
                        target_point = current_point
                        target_point[0] += 0.002
                        self.rob.movel(target_point, acc=a, vel=v0, wait=False)
                        t1 = time()
                        Utility.formatPrinting("wait_message << downSend_MoveRight :: target " + stateMachine + " >> " + " ".join(map(str,target_point)))
                        
                        while GUI.quitApplication == 0:
                            current_point = self.rob.getl()
                            t2 = time()
                            if (current_point[0] - target_point[0] <= 0.0001) or (t2 - t1) <= 1:
                                GUI.send_lock.acquire()
                                GUI.sendMessageQueue.put("MoveComplete")
                                GUI.send_lock.release()
                                break

                    if task_num == 2 and enableMove == 1:
                        if direction != 1:
                            direction = 1
                            current_point = self.rob.getl()
                            target_point = current_point
                            target_point[0] = hand_x_right_limit  # y change var
                            self.rob.movel(target_point, acc=a, vel=0.03, wait=False)
                            Utility.formatPrinting("wait_message << downSend_MoveRight :: target " + stateMachine + " >> " + " ".join(map(str,target_point)))
                
                elif this_message == "downSend_HandStop":
                    if (task_num == 1 and task_sub_step == 3) or (task_num == 1 and task_sub_step == 5):
                        self.rob.stopl(acc=a)  
                        current_point = self.rob.getl()
                        Utility.formatPrinting("wait_message << downSend_HandStop :: current " + stateMachine + " >> " + " ".join(map(str,target_point)))
                        GUI.send_lock.acquire()
                        GUI.sendMessageQueue.put("MoveComplete")
                        GUI.send_lock.release()
                    if enableMove == 1:
                        if direction != 0:
                            self.rob.stopl(acc=a)
                            direction = 0
                            current_point = self.rob.getl()
                            Utility.formatPrinting("wait_message << downSend_HandStop :: current " + stateMachine + " >> " + " ".join(map(str,target_point)))

                elif this_message == "downSend_NoHandStop":
                    if (task_num == 1 and task_sub_step == 3) or (task_num == 1 and task_sub_step == 5):
                        self.rob.stopl(acc=a)  
                        current_point = self.rob.getl()
                        Utility.formatPrinting("wait_message << downSend_HandStop :: current " + stateMachine + " >> " + " ".join(map(str,target_point)))
                        GUI.send_lock.acquire()
                        GUI.sendMessageQueue.put("MoveComplete")
                        GUI.send_lock.release() 
                    if enableMove == 1:
                        if direction != 0:
                            self.rob.stopl(acc=a)
                            direction = 0
                            current_point = self.rob.getl()
                            Utility.formatPrinting("wait_message << downSend_NoHandStop :: current " + stateMachine + " >> " + " ".join(map(str,target_point)))

            elif status == "task_end":
                if flag_pointcloud == True:
                    task_num = 1
                else:
                    task_num = 2
                task_sub_step = 0
                
                if task_num == 0:   # task_end状态，第一次执行需要等待开始键。需要跳过第一个状态
                    task_sub_step = 1
                # task_num_break = 0   # 不回原点
                status = task_list[task_num][task_sub_step]
                current_point = self.rob.getl()
                Utility.formatPrinting("task_end " + status + " >> " + " ".join(map(str,target_point)))

            GUI.stateMachine_Lock.acquire()
            if stateMachine == "Btn_UI_Stop":
                stateMachine = "UI_Stop"
            else:
                stateMachine = status
            GUI.stateMachine_Lock.release()

            sleep(0.001)
        self.rob.close()
        print("URRobotThread quit")
        