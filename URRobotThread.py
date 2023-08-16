import urx
import GUI, Utility
import UartProtocolParseThread
import TransformCoordinateThread
import numpy as np

from time import sleep
from threading import Thread

stateMachine = ""
task_num = 0
task_sub_step = 0


class URRobotThread(Thread):
    def __init__(self):
        print("URRobotThread.__init__")
        Thread.__init__(self)
        self.rob = urx.Robot("192.168.1.100")
                
    def run(self):
        print("URRobotThread.run")
        global stateMachine, task_num, task_sub_step

        task_list = [
            ["wait_start_btn", "move_z", "move_y", "move_x", "send_message", "wait_message","move_z", "send_message",
             "wait_message", "task_end"],

            ["move_x", "move_y","send_message", "wait_message", "send_message", "wait_message", "move_z", "send_message",
             "move_y", "move_x", "move_y", "wait_message", "send_message", "wait_message", "move_z", "send_message", 
             "wait_message", "move_y", "move_x", "task_end"],

            ["move_x", "move_y", "send_message", "wait_message", "move_x", "move_y", "send_message", "wait_message",
             "send_message", "wait_message", "task_end"],

            ["move_y", "send_message", "wait_message", "move_z", "send_message", "wait_message", "move_x", "task_end"]]

        message_list = [
            ["", "", "", "", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete", ""],

            ["", "", "StartPrepare", "downSend_PrepareComplete", "StartGrab", "downSend_GrabComplete", "", "LiftComplete", "", 
             "", "", "downSend_RequestDecline", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete",
             "", "", ""],

            ["", "", "HandInteraction", "downSend_RequestDecline", "", "", "StartDecline", "downReply_StartDecline",
             "CompleteDecline", "downSend_TaskComplete",""],

            ["", "StartDecline", "downReply_StartDecline", "", "CompleteDecline", "downSend_TaskComplete", "", ""]]

        position_list = [
            [[0, 0, 0, 0, 0, 0], [0, 0, 0.275, 0, 0, 0], [0, -0.268, 0, 0, 0, 0], [-0.107, 0, 0, 1.208, 1.201, -1.233],
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.117, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],

            [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
             [0, 0, 0.275, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, -0.268, 0, 0, 0, 0], [-0.386, 0, 0, 0, 0, 0], [0, -0.496, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.117, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
             [0, -0.268, 0, 0, 0, 0], [-0.107, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],

            [[-0.156, 0, 0, 0, 0, 0], [0, -0.566, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [-0.156, 0, 0, 0, 0, 0], [0, -0.268, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]],

            [[0, -0.268, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0.117, 0, 0, 0], [0, 0, 0, 0, 0, 0],
             [-0.107, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]]
        
        hand_x_left_limit = -0.236
        hand_x_right_limit = -0.076

        x_left_limit = -0.016         # -0.410
        x_right_limit = 0.426         # 0.436
        y_end_limit = -0.696          # -0.690
        y_front_limit = -0.366        # -0.268
    
        y1 = -0.469
        y2 = -0.629
        task_num_break = 0

        a = 0.05
        v0 = 0.02
        v1 = 0.05
        v2 = 0.2
        direction = 0
        zMoveDirection = 0

        lastmoveSource = 0
        moveSource = 0
        enableMove = 0
        pointcloud2 = np.array([-0.107, -0.568, 0.117])
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

            if status == "move_z":
                current_point = self.rob.getl()
                target_point = [current_point[0],current_point[1],current_point[2],current_point[3],current_point[4],current_point[5]]
                target_point[2] = position_list[task_num][task_sub_step][2]  # z change var
                
                if target_point[2] > current_point[2]:  # lift
                    v = 0.01 # v0                       # slow lift
                    zMoveDirection = 1
                    a = 0.1
                    source_point = current_point
                else:
                    a = 0.05
                    v = v1                              # fast down
                    zMoveDirection = -1

                self.rob.movel(target_point, acc=a, vel=v, wait=False)
                status = "wait_move_z"
                
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
                target_point[2] = 0.117
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
                if task_num == 0 and task_sub_step == 3:            # change pose
                    target_point[3] = position_list[task_num][task_sub_step][3]
                    target_point[4] = position_list[task_num][task_sub_step][4]
                    target_point[5] = position_list[task_num][task_sub_step][5]
                ##################################################################

                if task_num == 1 and task_sub_step == 0:
                    target_point[0] = pointcloud2[0]
                    
                if not np.isnan(target_point).any():
                    self.rob.movel(target_point, acc=a, vel=v2, wait=False)
                    status = "wait_move_x"
                else:
                    status = "task_end"
                
            elif status == "wait_move_x":
                current_point = self.rob.getl()
                # 判断移动目标值是否到达指定位置
                if abs(current_point[0] - target_point[0]) < 0.005:
                    task_sub_step += 1  
                    status = task_list[task_num][task_sub_step]  
                # 判断没有抓取任务，保持人手互动任务    
                if task_num == 2 and flag_pointcloud == False and task_sub_step == 5:
                    task_sub_step = 2
                    status = task_list[task_num][task_sub_step]   
        
            elif status == "move_y":
                current_point = self.rob.getl()
                target_point = current_point
                target_point[1] = position_list[task_num][task_sub_step][1]  
                # if task_num_break == 1:
                #     target_point[1] = y1
                # if task_num_break == 2:
                #     target_point[1] = y2

                if task_num == 1 and task_sub_step == 1:
                    target_point[1] = pointcloud2[1]
                    
                if not np.isnan(target_point).any():
                    self.rob.movel(target_point, acc=a, vel=v2, wait=False)
                    status = "wait_move_y"
                else:
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

                if this_message == message_list[task_num][task_sub_step]:
                    Utility.formatPrinting("wait_message << << " + message_list[task_num][task_sub_step])
                    task_sub_step += 1
                    status = task_list[task_num][task_sub_step]
                    if this_message == "downSend_GrabComplete":
                        GUI.displayPictureName = "Stable"

                elif this_message == "downReply_StartPrepare":
                    Utility.formatPrinting("wait_message << downReply_StartPrepare")
                elif this_message == "downSend_PrepareGrabDemo":
                    Utility.formatPrinting("wait_message << downSend_PrepareGrabDemo")
                elif this_message == "downSend_PrepareComplete":
                    GUI.displayPictureName = "Nothing"
                    Utility.formatPrinting("wait_message << downSend_PrepareComplete")
                elif this_message == "downReply_StartGrab":
                    GUI.displayPictureName = "Grabbing"
                    Utility.formatPrinting("wait_message << downReply_StartGrab")
                elif this_message == "downSend_GripperState":
                    if UartProtocolParseThread.someThing == 1:  # gripperDistance
                        GUI.displayPictureName = "Something"
                    else:  # gripperDistance
                        GUI.displayPictureName = "Nothing"
                    Utility.formatPrinting("wait_message << downSend_GripperState")
                elif this_message == "downSend_GrabComplete":
                    Utility.formatPrinting("wait_message << downSend_GrabComplete")
                    GUI.displayPictureName = "Stable"
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
                elif this_message == "downSend_RequestDecline":
                    Utility.formatPrinting("wait_message << downSend_RequestDecline")
                elif this_message == "downReply_StartDecline":
                    Utility.formatPrinting("wait_message << downReply_StartDecline")
                elif this_message == "downReply_CompleteDecline":
                    Utility.formatPrinting("wait_message << downReply_CompleteDecline")
                elif this_message == "downSend_GripperOpenComplete":
                    Utility.formatPrinting("wait_message << downSend_GripperOpenComplete")
                # 没有物品时的任务结束
                elif this_message == "downSend_TaskComplete":   # exception complete
                    Utility.formatPrinting("wait_message << downSend_TaskComplete")
                    if task_num == 1:
                        task_sub_step = 14
                        status = task_list[task_num][task_sub_step]
                elif this_message == "downReply_UIStop":
                    Utility.formatPrinting("wait_message << downReply_UIStop")
                elif this_message == "downReply_HandInteraction":
                    Utility.formatPrinting("wait_message << downReply_HandInteraction")
                elif this_message == "downReply_MutualCapacitanceClean":
                    Utility.formatPrinting("wait_message << downReply_MutualCapacitanceClean")
                
                elif this_message == "downSend_MoveLeft":
                    if enableMove == 1:
                        if direction != -1:
                            direction = -1
                            current_point = self.rob.getl()
                            target_point = current_point
                            target_point[0] = hand_x_left_limit
                            self.rob.movel(target_point, acc=a, vel=v0, wait=False)
                            Utility.formatPrinting("wait_message << downSend_MoveLeft :: target " + stateMachine + " >> " + " ".join(map(str,target_point)))

                elif this_message == "downSend_MoveRight":
                    if enableMove == 1:
                        if direction != 1:
                            direction = 1
                            current_point = self.rob.getl()
                            target_point = current_point
                            target_point[0] = hand_x_right_limit  # y change var
                            self.rob.movel(target_point, acc=a, vel=v0, wait=False)
                            Utility.formatPrinting("wait_message << downSend_MoveRight :: target " + stateMachine + " >> " + " ".join(map(str,target_point)))

                elif this_message == "downSend_HandStop":
                    if enableMove == 1:
                        if direction != 0:
                            self.rob.stopl(acc=a)
                            direction = 0
                            current_point = self.rob.getl()
                            Utility.formatPrinting("wait_message << downSend_HandStop :: current " + stateMachine + " >> " + " ".join(map(str,target_point)))

                elif this_message == "downSend_NoHandStop":
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
                # task_num_break = 0
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
        print("UartReceiveThread quit")
        