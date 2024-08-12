import cv2
import base64
import time
from car_actions import LeftRightServo_appointed_detection
from multimodal import call_openai_api



PROMPT= '''
你是我的智能小车助手，我有以下功能，请你根据我的指令，以json形式输出要运行的对应函数和你给我的回复

【以下是所有内置函数介绍】
- 初始化GPIO引脚和PWM通道：`init()`
- 小车前进：`run(speed=80)` 
  - 参数：`speed`（可选） - 控制小车前进的速度，占空比（0-100%）。
- 小车后退：`back(speed=80)` 
  - 参数：`speed`（可选） - 控制小车后退的速度，占空比（0-100%）。
- 小车左转：`left(speed=80)` 
  - 参数：`speed`（可选） - 控制小车左转的速度，占空比（0-100%）。
- 小车右转：`right(speed=80)` 
  - 参数：`speed`（可选） - 控制小车右转的速度，占空比（0-100%）。
- 小车刹车：`brake()` 
  - 无参数 - 停止小车运动。
- 设置摄像头舵机到指定位置：`servo_appointed_detection(pwm, pos)` 
  - 参数：
    - `pwm` - 对应的 PWM 对象。可能的值：`pwm_UpDownServo`（摄像头上下舵机）和 `pwm_LeftRightServo`（摄像头左右舵机）。（如果没有特别声明，默认调用pwm_LeftRightServo）
    - `pos` - 舵机的目标位置（0-180度）。
- 设置前舵机到指定位置：`frontservo_appointed_detection(pos)` 
  - 参数：`pos` - 前舵机的目标位置（0-180度）。
- 测量超声波距离：`Distance_test()` 
  - 无参数 - 测量距离并打印结果。
- 设置RGB LED灯颜色：`color_led_pwm(iRed, iGreen, iBlue)` 
  - 参数：`iRed` - 红色分量（0-255）；`iGreen` - 绿色分量（0-255）；`iBlue` - 蓝色分量（0-255）。
- 控制蜂鸣器发声：`whistle()` 
  - 无参数 - 蜂鸣器发声。
- 处理视频流，打开摄像头并录制视频：`video_stream()` 
  - 无参数 - 捕捉摄像头画面并保存到视频文件。
- 启动视频录制线程：`start_video_stream()` 
  - 无参数 - 启动一个线程来录制视频。
- 停止视频录制线程：`stop_video_stream()` 
  - 无参数 - 停止录制视频并关闭视频流线程。


【输出json格式】
你直接输出json即可，从{开始，不要输出包含```json的开头或结尾
在'function'键中，输出函数名列表，列表中每个元素都是字符串，代表要运行的函数名称和参数。每个函数既可以单独运行，也可以和其他函数先后运行。列表元素的先后顺序，表示执行函数的先后顺序
在'response'键中，根据我的指令和你编排的动作，以第一人称输出你回复我的话，不要超过20个字，可以幽默和发散，用上歌词、台词、互联网热梗、名场面。比如李云龙的台词、甄嬛传的台词、练习时长两年半。

【以下是一些具体的例子】
我的指令：帮我找到一台电脑。{
  "function": [
    "start_video_stream()",
    "run(speed=80)",
    "time.sleep(2)",
    "right(speed=80)",
    "time.sleep(1)"
  ],
  "response": "小车左右环顾，找到电脑立刻停下。"
}
'''




def open_camera(ip_address, port_number):
    """
    打开摄像头视频流并返回视频捕获对象
    :param ip_address: 摄像头IP地址
    :param port_number: 摄像头端口
    :return: 返回视频捕获对象，如果失败返回None
    """
    cap = cv2.VideoCapture(f'http://{ip_address}:{port_number}/?action=stream')
    if not cap.isOpened():
        print("无法打开摄像头")
        return None
    return cap


def analyze_image(cap):
    """
    捕获当前摄像头的图像（正前方、左转90度、右转180度），并调用OpenAI API进行分析
    :param cap: 已经打开的摄像头视频捕获对象
    :return: 返回分析结果
    """
    if cap is None:
        print("摄像头对象无效")
        return None

    # 捕获正前方的图像
    ret, frame_center = cap.read()
    if not ret:
        print("无法读取正前方的帧")
        return None

    # 控制摄像头向左转90度，并捕获图像
    LeftRightServo_appointed_detection(0)  # 向左转90度
    time.sleep(1)  # 等待摄像头稳定
    ret, frame_left = cap.read()
    if not ret:
        print("无法读取左侧帧")
        return None

    # 控制摄像头向右转180度（从左转90度的位置开始），并捕获图像
    LeftRightServo_appointed_detection(180)  # 向右转180度
    time.sleep(1)  # 等待摄像头稳定
    ret, frame_right = cap.read()
    if not ret:
        print("无法读取右侧帧")
        return None

    # 将摄像头复位到初始位置
    LeftRightServo_appointed_detection(90)  # 复位到正前方

    # 将三帧图片编码为Base64格式
    _, buffer_center = cv2.imencode('.jpg', frame_center)
    image_base64_center = base64.b64encode(buffer_center).decode('utf-8')

    _, buffer_left = cv2.imencode('.jpg', frame_left)
    image_base64_left = base64.b64encode(buffer_left).decode('utf-8')

    _, buffer_right = cv2.imencode('.jpg', frame_right)
    image_base64_right = base64.b64encode(buffer_right).decode('utf-8')

    #释放摄像头资源
    cap.release()

    # 调用API进行分析，传递三个图像数据
    result = call_openai_api([image_base64_center, image_base64_left, image_base64_right], PROMPT)

    # 关闭OpenCV显示窗口
    cv2.destroyAllWindows()

    return result



