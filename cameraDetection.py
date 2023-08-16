# coding: utf-8

import os
import shutil
import time
from pathlib import Path

import cv2
import torch
import numpy as np
import Utility

from yolov5.models.experimental import attempt_load
from yolov5.utils.general import (
    check_img_size, non_max_suppression, apply_classifier, scale_labels,
    xyxy2xywh, plot_one_rotated_box, strip_optimizer, set_logging)
from yolov5.utils.torch_utils import select_device
from yolov5.utils.evaluation_utils import rbox2txt


class Object(object):
    def __init__(self):
        self.conf = 0.0
        self.label = " "
        self.angle = 0
        self.row = 0
        self.col = 0
        self.cls = 0

obj = Object()

class CameraDetection:
    def __init__(self):
        self.weights = "/home/ts/wzy/ts_ur/yolov5/weights/best.pt"
        self.source = "./yolov5/det_images"                   #测试数据，可以是图片/视频路径，也可以是'0'(电脑自带摄像头),也可以是rtsp等视频流
        self.output = "./yolov5/inference/detection/"         #网络预测之后的图片/视频的保存路径
        self.img_size = 512             #网络输入图片大小
        self.conf_thres = 0.8           #置信度阈值
        self.iou_thres = 0.45           #做nms的iou阈值
        self.device = '0,1'
        self.view_img = False           #是否展示预测之后的图片/视频，默认False
        self.save_txt = True  
        self.save_img = True          #是否将预测的框坐标以txt文件形式保存，默认False
        self.classes = None             #设置只保留某一部分类别，形如0或者0 2 3
        self.agnostic_nms = False       #进行nms是否将所有类别框一视同仁，默认False
        self.augment = False            #推理的时候进行多尺度，翻转等操作(TTA)推理
        self.update = False             #如果为True，则对所有模型进行strip_optimizer操作，去除pt文件中的优化器等信息，默认为False

        self.crop_x = 0              #图像裁剪参数
        self.crop_y = 0
        self.crop_width = 280
        self.crop_height = 390
        set_logging()
        

    def create_output_floder(self):
        if os.path.exists(self.output):
            shutil.rmtree(self.output)  # delete output folder
        os.makedirs(self.output)  # make new output folder

        if os.path.exists(self.source):
            shutil.rmtree(self.source)
        os.makedirs(self.source)


    #-------- 建立yolo模型，载入yolo模型的权重 -------#
    def load_model(self):

        device = select_device(self.device)
        # 如果设备为gpu，使用Float16
        half = device.type != 'cpu'  # half precision only supported on CUDA

        # 加载Float32模型，确保用户设定的输入图片分辨率能整除最大步长s=32(如不能则调整为能整除并返回)
        model = attempt_load(self.weights, map_location=device)  # load FP32 model
        self.img_size = check_img_size(self.img_size, s=model.stride.max())  # check img_size
        # 设置Float16
        if half:
            model.half()  # to FP16

        # 获取类别名字    names = ['person', 'bicycle', 'car',...,'toothbrush']
        names = model.module.names if hasattr(model, 'module') else model.names
        # 设置画框的颜色    colors = [[178, 63, 143], [25, 184, 176], [238, 152, 129],....,[235, 137, 120]]随机设置RGB颜色
        colors = [[np.random.randint(0, 255) for _ in range(3)] for _ in range(len(names))]

        # 进行一次前向推理,测试程序是否正常  向量维度（1，3，imgsz，imgsz）
        img = torch.zeros((1, 3, self.img_size, self.img_size), device=device)  # init img
        _ = model(img.half() if half else img) if device.type != 'cpu' else None  # run once
  
        return half, model, names, colors, device


    # Process detections
    def process_detections(self, pred, colors, names, t2, t1, img, img_raw):
        
        for i, det in enumerate(pred):  # i:image index  det:(num_nms_boxes, [xylsθ,conf,classid]) θ∈[0,179]
            p, s, im0 = '', '', img_raw
            
            t = time.time()
            save_path = str(Path(self.output)) + "/" +str(t) + ".jpg"  # 图片保存路径+图片名字
            # txt_path = str(Path(self.output) / Path(p).stem) + ('_%g' % dataset.frame if dataset.mode == 'video' else '')
            
            s += '%gx%g ' % img.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh

            if det is None:
                obj.conf = 0.0
                obj.label = " "
                obj.angle = 0
                obj.row = 0
                obj.col = 0
                obj.cls = 0
                return None
            
            if det is not None and len(det):
                Utility.formatPrinting("Processing detect result ...")
                # Rescale boxes from img_size to im0 size
                det[:, :5] = scale_labels(img.shape[2:], det[:, :5], im0.shape).round()

                # Print results    det:(num_nms_boxes, [xylsθ,conf,classid]) θ∈[0,179]
                for c in det[:, -1].unique():  # unique函数去除其中重复的元素，并按元素（类别）由大到小返回一个新的无元素重复的元组或者列表
                    n = (det[:, -1] == c).sum()  # detections per class  每个类别检测出来的素含量
                    s += '%g %ss, ' % (n, names[int(c)])  # add to string 输出‘数量 类别,’

                # Write results  det:(num_nms_boxes, [xywhθ,conf,classid]) θ∈[0,179]
                for *rbox, conf, cls in reversed(det):  # 翻转list的排列结果,改为类别由小到大的排列
                
                    if self.save_img or self.view_img:  # Add bbox to image
                        label = '%s %.2f' % (names[int(cls)], conf)
                        classname = '%s' % names[int(cls)]
                        conf_str = '%.3f' % conf
                        rbox2txt(rbox, classname, conf_str, str(t), str(self.output + '/result_txt'))
                        #plot_one_box(rbox, im0, label=label, color=colors[int(cls)], line_thickness=2)
                        plot_one_rotated_box(rbox, im0, label=label, color=colors[int(cls)], line_thickness=1,
                                            pi_format=False)
                        
                        obj.conf = float('%.3f' % conf)
                        obj.label = classname
                        obj.angle = int(180-rbox[-1])
                        obj.row = int(rbox[1])
                        obj.col = int(rbox[0])
                        obj.cls = int(cls)

                        Utility.formatPrinting("conf :" + str(obj.conf) + "\t label :" + str(obj.label))

            # Print time (inference + NMS)
            Utility.formatPrinting('%sDone. (%.3fs)' % (s, t2 - t1))

            # Stream results 播放结果
            if self.view_img:
                cv2.imshow(p, im0)
                if cv2.waitKey(1) == ord('q'):  # q to quit
                    raise StopIteration

            # Save results (image with detections)
            if self.save_img:
                cv2.imwrite(save_path, im0)


