# coding: utf-8

import yaml
import time
import sys
import numpy as np
import cv2
from threading import Thread, Lock
from pathlib import Path

import torch
from yolov5.utils.datasets import letterbox
from yolov5.utils.torch_utils import time_synchronized
from yolov5.utils.general import rotate_non_max_suppression

from kinect2Bridge import Kinect2Bridge
from cameraDetection import CameraDetection
import Utility, GUI, cameraDetection

from scipy.spatial.transform import Rotation 
from pylibfreenect2 import FrameType, Freenect2, SyncMultiFrameListener, Registration, Frame
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel

try:
    from pylibfreenect2 import OpenGLPacketPipeline
    packetPipeline = OpenGLPacketPipeline()
except:
    try:
        from pylibfreenect2 import OpenCLPacketPipeline
        packetPipeline = OpenCLPacketPipeline()
    except:
        try:
            from pylibfreenect2 import CudaPacketPipeline
            packetPipeline = CudaPacketPipeline()
        except:
            from pylibfreenect2 import CpuPacketPipeline
            packetPipeline = CpuPacketPipeline()
print("Packet pipeline:", type(packetPipeline).__name__)

# Create and set logger
logger = createConsoleLogger(LoggerLevel.Debug)
setGlobalLogger(logger)

pointCloud_lock = Lock()
pointcloud = np.array([-0.107, -0.368, 0.117])


def loadHandeyeCalibrationFile(filename):
    with open(filename, "r" , encoding='utf8') as f:
        return yaml.safe_load(f.read())


class TransformCoordThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.filename = "./data/ur5_kinect_handeyecalibration_eye_on_base.yaml"
        res = loadHandeyeCalibrationFile(self.filename)
        self.qw = res['transformation']['qw']
        self.qx = res['transformation']['qx']
        self.qy = res['transformation']['qy']
        self.qz = res['transformation']['qz']
        self.x = res['transformation']['x']
        self.y = res['transformation']['y']
        self.z = res['transformation']['z']

        self.start()
        
    def run(self):
        global pointcloud
        
        kinect = Kinect2Bridge("/home/ts/wzy/ts_ur/data/")
        
        fn = Freenect2()
        num_devices = fn.enumerateDevices()
        if num_devices <= 0:
            print("No Kinect2 devices found!")
        assert num_devices > 0

        if kinect.sensor == " ":
            kinect.sensor = fn.getDefaultDeviceSerialNumber();
        kinect.sensor = fn.getDeviceSerialNumber(0)
        print("serial : ", kinect.sensor.decode())
        device = fn.openDevice(kinect.sensor, pipeline=packetPipeline)      #启动设备

        if device == 0:
            print("No device connected or failure opening the default one!")

        if kinect.enable_rgb:
            kinect.types |= FrameType.Color
        if kinect.enable_depth:
            kinect.types |= (FrameType.Ir | FrameType.Depth)
        listener = SyncMultiFrameListener(kinect.types)

        # Register listeners
        device.setColorFrameListener(listener)
        device.setIrAndDepthFrameListener(listener)

        print("starting kinect2")
        if kinect.enable_rgb and kinect.enable_depth:
            device.start()     #启动数据传输
        else:
            device.startStreams(rgb=kinect.enable_rgb, depth=kinect.enable_depth)

        irParams = device.getIrCameraParams()
        colorParams = device.getColorCameraParams()

        # NOTE: must be called after device.start()
        if kinect.enable_depth:
            registration = Registration(irParams, colorParams)      #循环接收

        undistorted = Frame(512, 424, 4)
        registered = Frame(512, 424, 4)
        kinect.initCalibration()
       
        detect = CameraDetection()
        detect.create_output_floder()
        half, model, names, colors, _device_ = detect.load_model()

        t_vec = np.array([self.x, self.y, self.z])     #[:, np.newaxis]
        Utility.formatPrinting("平移向量 ：" + str(t_vec))

        r = Rotation.from_quat([self.qx, self.qy, self.qz, self.qw])
        rotation_matrix = r.as_matrix()
        # rotation_matrix = np.linalg.inv(rotation_matrix)
        
        # [ 0.06394225 -0.20092473  0.87039896] 机械臂坐标起始原点，在相机坐标系下的坐标值
        X = 0.06394225
        Y = -0.20092473
        Z = 0.87039896

        while GUI.quitApplication == 0:

            frames = listener.waitForNewFrame()
            if kinect.enable_rgb:
                color = frames[FrameType.Color]
            if kinect.enable_depth:    
                ir = frames[FrameType.Ir]
                depth = frames[FrameType.Depth]

            if kinect.enable_rgb and kinect.enable_depth:
                registration.apply(color, depth, undistorted, registered,
                                    bigdepth=kinect.bigdepth,
                                    color_depth_map=kinect.color_depth_map)
                
                # img_raw = cv2.cvtColor(color.asarray(), cv2.COLOR_BGRA2BGR)
                img_raw = cv2.cvtColor(registered.asarray(np.uint8), cv2.COLOR_BGRA2BGR)
                img_crop = img_raw[detect.crop_y:detect.crop_height, detect.crop_x:detect.crop_width]
                img_raw = np.pad(img_crop, ((0, kinect.depthHeight - detect.crop_height),(0, kinect.depthWidth - detect.crop_width),(0,0)),"constant", constant_values=125)
               
            elif kinect.enable_depth:
                registration.undistortDepth(depth, undistorted)  

            # Padded resize
            img = letterbox(img_raw, new_shape=detect.img_size)[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
            img = np.ascontiguousarray(img)
            Utility.formatPrinting(str(img.shape))

            img = torch.from_numpy(img).to(_device_)
            # 图片也设置为Float16
            img = img.half() if half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            # 没有batch_size的话则在最前面添加一个轴
            if img.ndimension() == 3:
                # (in_channels,size1,size2) to (1,in_channels,img_height,img_weight)
                img = img.unsqueeze(0)  # 在[0]维增加一个维度

            # Run inference
            t0 = time.time()
            t1 = time_synchronized()

            """
            model:
            input: in_tensor (batch_size, 3, img_height, img_weight)
            output: 推理时返回 [z,x]
            z tensor: [small+medium+large_inference]  size=(batch_size, 3 * (small_size1*small_size2 + medium_size1*medium_size2 + large_size1*large_size2), nc)
            x list: [small_forward, medium_forward, large_forward]  eg:small_forward.size=( batch_size, 3种scale框, size1, size2, [xywh,score,num_classes]) 
                
            前向传播 返回pred[0]的shape是(1, num_boxes, nc)
            h,w为传入网络图片的长和宽，注意dataset在检测时使用了矩形推理，所以这里h不一定等于w
            num_boxes = 3 * h/32 * w/32 + 3 * h/16 * w/16 + 3 * h/8 * w/8
            pred[0][..., 0:4] 预测框坐标为xywh(中心点+宽长)格式
            pred[0][..., 4]为objectness置信度
            pred[0][..., 5:5+nc]为分类结果
            pred[0][..., 5+nc:]为Θ分类结果
            """

            # pred : (batch_size, num_boxes, no)  batch_size=1
            Utility.formatPrinting("Start inference ...")
            pred = model(img, augment=detect.augment)[0]
            pred = rotate_non_max_suppression(pred, detect.conf_thres, detect.iou_thres, classes=detect.classes, agnostic=detect.agnostic_nms, without_iouthres=False)
            t2 = time_synchronized()

            detect.process_detections(pred, colors, names, t2, t1, img, img_raw)
            
            pointCloud_lock.acquire()
            X, Y, Z, B, G, R = registration.getPointXYZRGB(undistorted, registered, cameraDetection.obj.row, cameraDetection.obj.col)  
            point3d = np.array([X, Y, Z])
            pointcloud = np.dot(rotation_matrix, point3d.T).T + t_vec

            # y坐标计算得出是一个正值，与机械臂运动方向相反，在这里做了取反操作，和减去夹爪的长度
            pointcloud[1] = -(pointcloud[1] - 0.195)
            # pointcloud = np.concatenate(pointcloud, np.array([obj.cls, obj.angle]))
            pointCloud_lock.release()
            Utility.formatPrinting("PUT pointcloud : " + str(pointcloud) + "\t" )
            
            if detect.save_txt or detect.save_img:
                Utility.formatPrinting('Results saved to %s' % Path(detect.output))

            Utility.formatPrinting('All Done. (%.3fs)' % (time.time() - t0))

            # kinect.visualImage(color, undistorted, registered)
            # kinect.visualPointCloud(depth, registration, undistorted, registered)

            listener.release(frames)

            key = cv2.waitKey(delay=1)
            if key == ord('q'):
                break
            time.sleep(3)
        
        device.stop()
        device.close()
        print("TransformCoordinateThread quit")
        sys.exit(0)
    
        
