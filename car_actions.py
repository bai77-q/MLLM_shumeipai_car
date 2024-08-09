# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
import time
import sys
import cv2
import threading
import logging

# 配置日志，设置日志等级为INFO，格式为时间戳、日志等级和消息内容
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化上下左右舵机的角度为90度
ServoLeftRightPos = 90
ServoUpDownPos = 90
g_frontServoPos = 90

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

    # 电机控制引脚初始化
    if 'pwm_ENA' not in globals() or pwm_ENA is None:
        pwm_ENA = GPIO.PWM(ENA, 2000)
        pwm_ENA.start(0)
    if 'pwm_ENB' not in globals() or pwm_ENB is None:
        pwm_ENB = GPIO.PWM(ENB, 2000)
        pwm_ENB.start(0)

    # 舵机控制引脚初始化
    if 'pwm_FrontServo' not in globals() or pwm_FrontServo is None:
        pwm_FrontServo = GPIO.PWM(FrontServoPin, 50)
        pwm_FrontServo.start(0)
    if 'pwm_UpDownServo' not in globals() or pwm_UpDownServo is None:
        pwm_UpDownServo = GPIO.PWM(ServoUpDownPin, 50)
        pwm_UpDownServo.start(0)
    if 'pwm_LeftRightServo' not in globals() or pwm_LeftRightServo is None:
        pwm_LeftRightServo = GPIO.PWM(ServoLeftRightPin, 50)
        pwm_LeftRightServo.start(0)

    # RGB LED控制引脚初始化
    if 'pwm_rled' not in globals() or pwm_rled is None:
        pwm_rled = GPIO.PWM(LED_R, 1000)
        pwm_rled.start(0)
    if 'pwm_gled' not in globals() or pwm_gled is None:
        pwm_gled = GPIO.PWM(LED_G, 1000)
        pwm_gled.start(0)
    if 'pwm_bled' not in globals() or pwm_bled is None:
        pwm_bled = GPIO.PWM(LED_B, 1000)
        pwm_bled.start(0)

    # 设置超声波测距引脚
    GPIO.setup(TrigPin, GPIO.OUT)
    GPIO.setup(EchoPin, GPIO.IN)

    print("Initialization complete")



def set_motor_state(IN1_state, IN2_state, IN3_state, IN4_state, speed=80):

    """
    设置电机状态和速度
    :param IN1_state: 电机1正向引脚状态（GPIO.HIGH/LOW）
    :param IN2_state: 电机1反向引脚状态（GPIO.HIGH/LOW）
    :param IN3_state: 电机2正向引脚状态（GPIO.HIGH/LOW）
    :param IN4_state: 电机2反向引脚状态（GPIO.HIGH/LOW）
    :param speed: PWM占空比，用于控制电机速度
    """
    GPIO.output(IN1, IN1_state)
    GPIO.output(IN2, IN2_state)
    GPIO.output(IN3, IN3_state)
    GPIO.output(IN4, IN4_state)
    pwm_ENA.ChangeDutyCycle(speed)
    pwm_ENB.ChangeDutyCycle(speed)


def run(speed=80):
    """
    小车前进
    :param speed: PWM占空比，用于控制电机速度
    """
    set_motor_state(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW, speed)


def back(speed=80):
    """
    小车后退
    :param speed: PWM占空比，用于控制电机速度
    """
    set_motor_state(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH, speed)


def left(speed=80):
    """
    小车左转
    :param speed: PWM占空比，用于控制电机速度
    """
    set_motor_state(GPIO.LOW, GPIO.LOW, GPIO.HIGH, GPIO.LOW, speed)


def right(speed=80):
    """
    小车右转
    :param speed: PWM占空比，用于控制电机速度
    """
    set_motor_state(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.LOW, speed)


def brake():
    """
    小车刹车（停止）
    """
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)


def servo_appointed_detection(pwm=None, pos=90):
    """
    控制舵机旋转到指定位置
    :param pwm: 舵机对应的PWM对象。如果未提供，则使用默认的pwm_LeftRightServo。
    :param pos: 目标位置角度（0-180度）
    """
    if pwm is None:
        pwm = pwm_LeftRightServo  # 使用默认的PWM对象

    if 0 <= pos <= 180:  # 检查角度范围
        pwm.ChangeDutyCycle(2.5 + 10 * pos / 180)
        time.sleep(0.02)
        pwm.ChangeDutyCycle(0)  # 固定当前位置
    else:
        logging.warning(f"Invalid servo position: {pos}. Must be between 0 and 180 degrees.")



def frontservo_appointed_detection(pos):
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
    测量距离并打印结果
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
    print("Distance is %d cm" % (((t2 - t1) * 340 / 2) * 100))


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
