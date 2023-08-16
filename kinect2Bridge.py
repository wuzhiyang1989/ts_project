# coding: utf-8

import numpy as np
import cv2
import time

import pcl
import pcl.pcl_visualization
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Frame

K2_CALIB_COLOR = "calib_color.yaml"
K2_CALIB_IR = "calib_ir.yaml"
K2_CALIB_POSE = "calib_pose.yaml"
K2_CALIB_DEPTH = "calib_depth.yaml"


class Kinect2Bridge:
    def __init__(self, calib_path):
        self.calib_path = calib_path
        self.source = "./yolov5/det_images/"
        self.depthShift = 0.0
        self.sensor = " "
        self.cameraMatrixColor = np.eye(3, dtype=float)
        self.distortionColor = np.zeros((1, 5), dtype=float)
        self.cameraMatrixIr = np.eye(3, dtype=float)
        self.distortionIr = np.zeros((1, 5), dtype=float)
        self.cameraMatrixDepth = np.eye(3, dtype=float)
        self.distortionDepth = np.zeros((1, 5), dtype=float)
        self.rotation = np.eye(3, dtype=float)
        self.translation = np.zeros((3, 1), dtype=float)
        self.colorWidth = 1920
        self.colorHeight = 1080
        self.irWidth = 512
        self.irHeight = 424
        self.depthWidth = 512
        self.depthHeight = 424

        self.types = 0
        self.enable_rgb = True
        self.enable_depth = True

        # Optinal parameters for registration  
        # set True if you need  (False)
        self.need_bigdepth = True
        self.need_color_depth_map = False

        self.bigdepth = Frame(1920, 1082, 4) if self.need_bigdepth else None
        self.color_depth_map = np.zeros((424, 512),  np.int32).ravel() \
            if self.need_color_depth_map else None


    def loadCalibrationFile(self, filename):
        cv_file = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
        if not cv_file:
            print("can't open calibration file: " + filename)
        else:
            res = {
                    "cameraMatrix": cv_file.getNode("cameraMatrix").mat(),
                    "distortionCoefficients": cv_file.getNode("distortionCoefficients").mat(),
                    "rotation": cv_file.getNode("rotation").mat(),
                    "projection": cv_file.getNode("projection").mat(),
                }
        return res


    def loadCalibrationPoseFile(self, filename):
        cv_file = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
        if not cv_file:
            print("can't open calibration pose file: " + filename)
        else:
            res = {
                    "rotation": cv_file.getNode("rotation").mat(),
                    "translation": cv_file.getNode("translation").mat(),
                    "essential": cv_file.getNode("essential").mat(),
                    "fundamental": cv_file.getNode("fundamental").mat(),
                }
        return res 


    def loadCalibrationDepthFile(self, filename):
        cv_file = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
        if not cv_file:
            print("can't open calibration depth file: " + filename)
        else:
            res = {
                    "depthShift": cv_file.getNode("depthShift").real()
                }
        self.depthShift = res["depthShift"]


    def initDevice(self, packetPipeline):
        fn = Freenect2()
        num_devices = fn.enumerateDevices()
        if num_devices <= 0:
            print("No Kinect2 devices found!")
        assert num_devices > 0

        if self.sensor == " ":
            self.sensor = fn.getDefaultDeviceSerialNumber();
        self.sensor = fn.getDeviceSerialNumber(0)
        print("serial : ", self.sensor.decode())
        device = fn.openDevice(self.sensor, pipeline=packetPipeline)      #启动设备

        if device == 0:
            print("No device connected or failure opening the default one!")

        if self.enable_rgb:
            self.types |= FrameType.Color
        if self.enable_depth:
            self.types |= (FrameType.Ir | FrameType.Depth)
        listener = SyncMultiFrameListener(self.types)

        # Register listeners
        device.setColorFrameListener(listener)
        device.setIrAndDepthFrameListener(listener)

        print("starting kinect2")
        if self.enable_rgb and self.enable_depth:
            device.start()     #启动数据传输
        else:
            device.startStreams(rgb=self.enable_rgb, depth=self.enable_depth)

        return device

    
    def initCameraParameter(self, colorParams, irParams):           
        self.cameraMatrixColor[0][0] = colorParams.fx
        self.cameraMatrixColor[1][1] = colorParams.fy
        self.cameraMatrixColor[0][2] = colorParams.cx
        self.cameraMatrixColor[1][2] = colorParams.cy
        self.cameraMatrixColor[2][2] = 1

        self.cameraMatrixIr[0][0] = irParams.fx
        self.cameraMatrixIr[1][1] = irParams.fy
        self.cameraMatrixIr[0][2] = irParams.cx
        self.cameraMatrixIr[1][2] = irParams.cy
        self.cameraMatrixIr[2][2] = 1

        self.distortionIr[0][0] = irParams.k1;
        self.distortionIr[0][1] = irParams.k2;
        self.distortionIr[0][2] = irParams.p1;
        self.distortionIr[0][3] = irParams.p2;
        self.distortionIr[0][4] = irParams.k3;
    
        self.cameraMatrixDepth = np.array(self.cameraMatrixIr, copy = True)    #self.cameraMatrixIr.clone()
        self.distortionDepth = np.array(self.distortionIr, copy = True)        #self.distortionIr.clone()
       

    def initCalibration(self):
        calibPath = self.calib_path + self.sensor.decode() + '/'
        color_filename = calibPath + K2_CALIB_COLOR
        ir_filename = calibPath + K2_CALIB_IR
        pose_filename = calibPath + K2_CALIB_POSE
        depth_filename = calibPath + K2_CALIB_DEPTH 

        if color_filename != " ":
            print("Using sensor defaults for color intrinsic parameters.")
            res = self.loadCalibrationFile(color_filename)
            self.cameraMatrixColor = res["cameraMatrix"]
            self.distortionColor = res["distortionCoefficients"]

        if ir_filename != " ":
            print("Using sensor defaults for ir intrinsic parameters.")
            res = self.loadCalibrationFile(ir_filename)
            self.cameraMatrixDepth = res["cameraMatrix"]
            self.distortionDepth = res["distortionCoefficients"]
         
        if pose_filename != " ":
            print("Using defaults for rotation and translation.")
            res = self.loadCalibrationPoseFile(pose_filename)
            self.rotation = res["rotation"]
            self.translation = res["translation"]

        if depth_filename != " ":
            print("Using defaults for depth shift.")
            self.loadCalibrationDepthFile(depth_filename)
            print("depth shift : ", self.depthShift)

        print(self.cameraMatrixColor)
        cameraMatrixLowRes = np.array(self.cameraMatrixColor, copy = True)    #self.cameraMatrixColor.clone();
        cameraMatrixLowRes[0][0] /= 2;
        cameraMatrixLowRes[1][1] /= 2;
        cameraMatrixLowRes[0][2] /= 2;
        cameraMatrixLowRes[1][2] /= 2;
        
        map1Color, map2Color = cv2.initUndistortRectifyMap(self.cameraMatrixColor, self.distortionColor, None, None,(self.colorWidth, self.colorHeight), cv2.CV_16SC2)
        map1Ir, map2Ir = cv2.initUndistortRectifyMap(self.cameraMatrixIr, self.distortionIr, None, None,(self.irWidth, self.irHeight), cv2.CV_32FC1)
        # map1LowRes, map2LowRes = cv2.initUndistortRectifyMap(self.cameraMatrixColor, self.distortionColor, None, None,(color.width / 2, color.height / 2), cv2.CV_32FC1)


    def visualImage(self, color, undistorted, registered):
        if self.enable_rgb:
            # color = cv2.flip(color, 1)
            # color = cv2.cvtColor(color,cv2.COLOR_BGRA2BGR)
            # color_rect = cv2.remap(color, map1Color, map2Color, interpolation=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
            cv2.imshow("color", cv2.resize(color.asarray(), 
                                            (int(1920 / 3), int(1080 / 3))))  
            cv2.imwrite(self.source + 'color_'+ str(time.time()) + ".jpg", color.asarray())
                            
        if self.enable_depth:
            # cv2.imshow("ir", ir.asarray() / 65535.)                 # 红外图    
            # cv2.imshow("depth", depth.asarray() / 4500.)            # 深度图            
            cv2.imshow("undistorted", undistorted.asarray(np.float32) / 4500.)

        if self.enable_rgb and self.enable_depth:
            cv2.imshow("registered", registered.asarray(np.uint8))       #彩色图注入深度图
        
        if self.need_bigdepth:
            cv2.imshow("bigdepth", cv2.resize(self.bigdepth.asarray(np.float32),        
                                            (int(1920 / 3), int(1082 / 3))))       #深度图转换为RGB
        if self.need_color_depth_map:
            cv2.imshow("color_depth_map", self.color_depth_map.reshape(424, 512))       #深度图（无失真）
    

    def visualPointCloud(self, depth, registration, undistorted, registered):
        d = depth.asarray()
        n_rows = d.shape[0]   #424
        n_columns = d.shape[1]  #512
        points = np.zeros((n_rows * n_columns, 3), dtype=np.float32)
        # colors = np.zeros((n_rows * n_columns, 3), dtype=np.float32)

        for row in range(n_rows):
            for col in range(n_columns):
                # X, Y, Z = registration.getPointXYZ(undistorted, r, c)
                X, Y, Z, B, G, R = registration.getPointXYZRGB(undistorted, registered, row, col)
                points[row * n_columns + col] = np.array([X, Y, Z])

        cloud = pcl.PointCloud(points)
        visualcolor = pcl.pcl_visualization.PointCloudColorHandleringCustom(cloud, 50, 125, 255)

        visual = pcl.pcl_visualization.PCLVisualizering
        vis_create_window = pcl.pcl_visualization.PCLVisualizering()       #初始化一个对象，这里是很重要的一步
        visual.AddPointCloud_ColorHandler(vis_create_window, cloud, visualcolor, id=b'cloud', viewport=0)     #id相当于这一批点云的句柄。添加点云及标签
        vis_create_window.SetPointCloudRenderingProperties(pcl.pcl_visualization.PCLVISUALIZER_POINT_SIZE, 2, b'cloud')    #设置点的大小
        # vis_create_window.SpinOnce() # 只会在手动旋转对象的时候暂停

        while not visual.WasStopped(vis_create_window):
            visual.Spin(vis_create_window)   # 如果采用这句的话，就会一直停在这，后面不会再运行
        vis_create_window.RemovePointCloud(b'cloud', 0)


