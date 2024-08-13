# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import sys
import cv2
import threading
import logging

# 配置日志，设置日志等级为INFO，格式为时间戳、日志等级和消息内容
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化上下左右舵机的角度为正前方
ServoLeftRightPos = 20
ServoUpDownPos = 65
g_frontServoPos = 80

# GPIO引脚定义，用于控制电机、舵机、LED、蜂鸣器等
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13

EchoPin = 0
TrigPin = 1

LED_R = 22
LED_G = 27
LED_B = 24

FrontServoPin = 23
ServoUpDownPin = 9
ServoLeftRightPin = 11

buzzer = 8

video_running = False  # 用于控制视频流的运行状态
video_thread = None  # 视频流线程
out = None  # 视频文件输出对象

# 设置GPIO口为BCM编码方式，GPIO引脚编号采用Broadcom SOC通道编号
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


def init():
    global pwm_ENA, pwm_ENB, pwm_FrontServo, pwm_UpDownServo, pwm_LeftRightServo
    global pwm_rled, pwm_gled, pwm_bled

    # 设置电机控制引脚为输出模式
    GPIO.setup(ENA, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ENB, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)

    # 设置舵机引脚为输出模式
    GPIO.setup(FrontServoPin, GPIO.OUT)
    GPIO.setup(ServoUpDownPin, GPIO.OUT)
    GPIO.setup(ServoLeftRightPin, GPIO.OUT)

    # 设置RGB LED引脚为输出模式
    GPIO.setup(LED_R, GPIO.OUT)
    GPIO.setup(LED_G, GPIO.OUT)
    GPIO.setup(LED_B, GPIO.OUT)

    # 设置蜂鸣器引脚为输出模式
    GPIO.setup(buzzer, GPIO.OUT)

    # 初始化PWM对象，确保在GPIO引脚设置为输出模式后创建
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_ENA.start(0)
    pwm_ENB.start(0)

    pwm_FrontServo = GPIO.PWM(FrontServoPin, 50)
    pwm_UpDownServo = GPIO.PWM(ServoUpDownPin, 50)
    pwm_LeftRightServo = GPIO.PWM(ServoLeftRightPin, 50)
    pwm_FrontServo.start(0)
    pwm_UpDownServo.start(0)
    pwm_LeftRightServo.start(0)

    pwm_rled = GPIO.PWM(LED_R, 1000)
    pwm_gled = GPIO.PWM(LED_G, 1000)
    pwm_bled = GPIO.PWM(LED_B, 1000)
    pwm_rled.start(0)
    pwm_gled.start(0)
    pwm_bled.start(0)

    # 设置超声波测距引脚
    GPIO.setup(TrigPin, GPIO.OUT)
    GPIO.setup(EchoPin, GPIO.IN)

    print("Initialization complete")

def run(speed=30):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(speed)
    pwm_ENB.ChangeDutyCycle(speed)


def back(speed=30):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(speed)
    pwm_ENB.ChangeDutyCycle(speed)


def left(speed=30):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(speed)
    pwm_ENB.ChangeDutyCycle(speed)


def right(speed=30):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(speed)
    pwm_ENB.ChangeDutyCycle(speed)


def brake():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)


def LeftRightServo_appointed_detection(pos=20):
    """
    控制舵机旋转到指定位置
    :param pos: 目标位置角度（0-180度）
    """

    if -10 <= pos <= 180:  # 检查角度范围
        for i in range(18):
            pwm_LeftRightServo.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)
        pwm_LeftRightServo.ChangeDutyCycle(0)  # 固定当前位置
    else:
        logging.warning(f"Invalid servo position: {pos}. Must be between 0 and 180 degrees.")

def UpDownServo_appointed_detection(pos=65):
    """
    控制舵机旋转到指定位置
    :param pwm: 舵机对应的PWM对象。如果未提供，则使用默认的pwm_LeftRightServo。
    :param pos: 目标位置角度（0-180度）
    """

    if 0 <= pos <= 180:  # 检查角度范围
        for i in range(18):
            pwm_UpDownServo.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)
        pwm_UpDownServo.ChangeDutyCycle(0)  # 固定当前位置
    else:
        logging.warning(f"Invalid servo position: {pos}. Must be between 0 and 180 degrees.")


def frontservo_appointed_detection(pos=80):
    # pwm_FrontServo = GPIO.PWM(FrontServoPin, 50)
    # pwm_FrontServo.start(0)
    """
    控制前舵机旋转到指定位置
    :param pos: 目标位置角度（0-180度）
    """
    if 0 <= pos <= 180:  # 检查角度范围
        for i in range(18):
            pwm_FrontServo.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)
        pwm_FrontServo.ChangeDutyCycle(0)  # 固定当前位置
    else:
        logging.warning(f"Invalid front servo position: {pos}. Must be between 0 and 180 degrees.")


def Distance_test():
    """
    测量距离并返回结果（单位：cm）
    """
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TrigPin, GPIO.LOW)

    while not GPIO.input(EchoPin):
        pass
    t1 = time.time()

    while GPIO.input(EchoPin):
        pass
    t2 = time.time()

    # 计算距离 (单位：cm)
    distance = ((t2 - t1) * 340 / 2) * 100

    print("Distance is %d cm" % distance)
    return distance


def color_led_pwm(iRed, iGreen, iBlue):
    """
    控制RGB LED颜色
    :param iRed: 红色分量（0-255）
    :param iGreen: 绿色分量（0-255）
    :param iBlue: 蓝色分量（0-255）
    """
    v_red = (100 * iRed) / 255
    v_green = (100 * iGreen) / 255
    v_blue = (100 * iBlue) / 255
    pwm_rled.ChangeDutyCycle(v_red)
    pwm_gled.ChangeDutyCycle(v_green)
    pwm_bled.ChangeDutyCycle(v_blue)
    time.sleep(0.02)


def whistle():
    """
    蜂鸣器鸣响
    """
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.001)


def video_stream():
    """
    视频流处理函数，捕捉摄像头画面并保存到视频文件
    """
    global video_running, out
    ip_address = '192.168.50.1'  # 摄像头IP地址
    port_number = 8080  # 摄像头端口

    # 打开摄像头视频流
    cap = cv2.VideoCapture(f'http://{ip_address}:{port_number}/?action=stream')
    if not cap.isOpened():
        logging.error("无法打开摄像头")
        video_running = False
        return

    # 使用 MJPG 编码格式保存视频
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

    while video_running:
        ret, frame = cap.read()
        if not ret:
            logging.error("无法读取帧")
            break

        output = cv2.resize(frame, (640, 480))
        out.write(output)
        cv2.imshow('Output', output)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    if out:
        out.release()
        out = None
    cv2.destroyAllWindows()
    video_running = False


def start_video_stream():
    """
    启动视频流线程
    """
    global video_running, video_thread
    if not video_running:
        video_running = True
        video_thread = threading.Thread(target=video_stream)
        video_thread.start()
        logging.info("Video streaming started.")


def stop_video_stream():
    """
    停止视频流线程
    """
    global video_running, video_thread
    if video_running:
        video_running = False
        if video_thread is not None:
            video_thread.join()
        logging.info("Video streaming stopped.")



# 主函数，初始化系统并控制小车的动作
if __name__ == "__main__":
    init()  # 初始化系统

    # 示例用法：控制小车的前进、转向和停止
    # run()  # 小车前进
    # time.sleep(2)
    #
    # left()  # 小车左转
    # time.sleep(1)
    #
    # right()  # 小车右转
    # time.sleep(1)
    #
    # back()  # 小车后退
    # time.sleep(2)
    #
    # brake()  # 小车停止
