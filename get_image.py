import cv2
import base64
import time
import requests
import numpy as np
from car_actions import *

def get_image():
    """
    通过HTTP请求捕获当前图像（正前方、左转90度、右转180度），并保存和返回Base64编码的图像数据。
    :return: 返回三个图像的Base64编码列表
    """
    ip_address = "192.168.50.1"  # 替换为实际摄像头的IP地址
    snapshot_url = f'http://{ip_address}:8080/?action=snapshot'

    try:
        # 捕获正前方的图像
        LeftRightServo_appointed_detection(20)  # 正前方
        UpDownServo_appointed_detection(65) # 摄像头上下在正中
        time.sleep(1)  # 等待摄像头稳定
        response = requests.get(snapshot_url)
        if response.status_code != 200:
            print("无法获取正前方的图像")
            return None
        np_arr = np.frombuffer(response.content, np.uint8)
        frame_center = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        cv2.imwrite('front_image.jpg', frame_center)  # 保存前方图像

        # 控制摄像头向左转90度，并捕获图像
        LeftRightServo_appointed_detection(110)  # 最左
        UpDownServo_appointed_detection(65)
        time.sleep(1)  # 等待摄像头稳定
        response = requests.get(snapshot_url)
        if response.status_code != 200:
            print("无法获取左侧的图像")
            return None
        np_arr = np.frombuffer(response.content, np.uint8)
        frame_left = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        cv2.imwrite('left_image.jpg', frame_left)  # 保存左侧图像

        # 控制摄像头向右转180度（从左转90度的位置开始），并捕获图像
        LeftRightServo_appointed_detection(-10)  # 最右
        UpDownServo_appointed_detection(65)
        time.sleep(1)  # 等待摄像头稳定
        response = requests.get(snapshot_url)
        if response.status_code != 200:
            print("无法获取右侧的图像")
            return None
        np_arr = np.frombuffer(response.content, np.uint8)
        frame_right = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        cv2.imwrite('right_image.jpg', frame_right)  # 保存右侧图像

        # 将摄像头复位到初始位置
        LeftRightServo_appointed_detection(20)  # 复位到正前方

        # 将三帧图片编码为Base64格式
        _, buffer_center = cv2.imencode('.jpg', frame_center)
        image_base64_center = base64.b64encode(buffer_center).decode('utf-8')

        _, buffer_left = cv2.imencode('.jpg', frame_left)
        image_base64_left = base64.b64encode(buffer_left).decode('utf-8')

        _, buffer_right = cv2.imencode('.jpg', frame_right)
        image_base64_right = base64.b64encode(buffer_right).decode('utf-8')

        # 组合三个图像的Base64编码
        result = image_base64_center, image_base64_left, image_base64_right

    except Exception as e:
        print(f"图像分析过程中发生错误: {e}")
        return None

    return result
