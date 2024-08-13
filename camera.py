import cv2
import base64
import time
from car_actions import LeftRightServo_appointed_detection

def analyze_image():
    """
    打开摄像头并捕获当前图像（正前方、左转90度、右转180度），然后调用OpenAI API进行分析
    :return: 返回分析结果
    """
    ip_address = "192.168.50.1"  # 替换为实际摄像头的IP地址
    port_number = 8080  # 替换为实际摄像头的端口号

    # 开启摄像头
    cap = cv2.VideoCapture(f'http://{ip_address}:{port_number}/?action=stream')
    if not cap.isOpened():
        print("无法打开摄像头")
        return None

    try:
        # 捕获正前方的图像
        LeftRightServo_appointed_detection(90)  # 正前方
        time.sleep(2)  # 等待摄像头稳定
        ret, frame_center = cap.read()
        if not ret:
            print("无法读取正前方的帧")
            return None
        cv2.imwrite('front_image.jpg', frame_center)  # 保存前方图像

        # 控制摄像头向左转90度，并捕获图像
        LeftRightServo_appointed_detection(0)  # 向左转90度
        time.sleep(2)  # 等待摄像头稳定
        ret, frame_left = cap.read()
        if not ret:
            print("无法读取左侧帧")
            return None
        cv2.imwrite('left_image.jpg', frame_left)  # 保存左侧图像

        # 控制摄像头向右转180度（从左转90度的位置开始），并捕获图像
        LeftRightServo_appointed_detection(180)  # 向右转180度
        time.sleep(2)  # 等待摄像头稳定
        ret, frame_right = cap.read()
        if not ret:
            print("无法读取右侧帧")
            return None
        cv2.imwrite('right_image.jpg', frame_right)  # 保存右侧图像

        # 将摄像头复位到初始位置
        LeftRightServo_appointed_detection(90)  # 复位到正前方

        # 将三帧图片编码为Base64格式
        _, buffer_center = cv2.imencode('.jpg', frame_center)
        image_base64_center = base64.b64encode(buffer_center).decode('utf-8')

        _, buffer_left = cv2.imencode('.jpg', frame_left)
        image_base64_left = base64.b64encode(buffer_left).decode('utf-8')

        _, buffer_right = cv2.imencode('.jpg', frame_right)
        image_base64_right = base64.b64encode(buffer_right).decode('utf-8')

        # 组合三个图像的Base64编码
        result = [image_base64_center, image_base64_left, image_base64_right]

    except Exception as e:
        print(f"图像分析过程中发生错误: {e}")
        return None

    finally:
        # 确保摄像头资源释放和窗口关闭
        cap.release()
        cv2.destroyAllWindows()

    return result
