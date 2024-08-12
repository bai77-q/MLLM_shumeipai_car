import cv2
import base64
import time
import openai
import requests

# IP摄像头的IP地址和端口号
ip_address = '192.168.50.1'
port_number = 8080

# 打开视频流
cap = cv2.VideoCapture(f'http://{ip_address}:{port_number}/?action=stream')

if not cap.isOpened():
    print("无法打开摄像头")
    exit()

# 初始化时间
start_time = time.time()

# OpenAI API设置
openai.api_base = "https://api.lingyiwanwu.com/v1"
openai.api_key = "013565e5b3154a8cb5f91e7113dbc04a"

# 系统提示词
SYSTEM_PROMPT = '''
我即将说一句给智能车的指令，你帮我从这句话中提取出目标物体，并从这张图中找到是否具有目标物体。如果有，则给出我抵达该目标物体的路线；如果没有，也请给出操作指令。

例如，如果我的指令是：请帮助我找到一个垃圾桶。
你输出这样的格式：
{
 "目标物体": "垃圾桶",
 "是否含有目标物体": "否",
 "操作指令": "前进50厘米，左转90度，前进20厘米"
}

只回复json本身即可，不要回复其它内容

我现在的指令是：
'''

PROMPT = '帮我找到一个红色的椅子'

def call_openai_api(image_base64, prompt):
    for _ in range(3):  # 尝试重试3次
        try:
            completion = openai.ChatCompletion.create(
                model="yi-vision",
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT + prompt
                    },
                    {
                        "role": "user",
                        "content": "",  # content可以为空
                        "name": "image",
                        "data": image_base64  # 将Base64编码的数据作为独立字段传递
                    }
                ]
            )
            return completion.choices[0].message['content']
        except openai.error.APIError as e:
            print(f"API Error: {e}, Retrying...")
            time.sleep(5)  # 等待5秒后重试
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}, Retrying...")
            time.sleep(5)
    return None  # 如果重试3次仍失败，返回None

def Multiagent_plan(order='帮我找到大门'):
    '''
    根据输入的指令生成多模态大模型的动作计划，并调用 OpenAI API。
    '''
    # 将输入指令作为PROMPT
    prompt = order

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取帧")
            break

        # 显示当前帧
        cv2.imshow('Output', frame)

        # 每5秒截取一次图片
        if time.time() - start_time >= 5:
            # 重置开始时间
            start_time = time.time()

            # 将当前帧编码为JPEG格式并存入内存
            _, buffer = cv2.imencode('.jpg', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            # 调用API
            result = call_openai_api(image_base64, prompt)
            if result:
                print(result)
                return result  # 返回结果以便进一步处理
            else:
                print("API调用失败")

        # 如果按下'q'键则退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放捕获对象，并关闭所有OpenCV窗口
    cap.release()
    cv2.destroyAllWindows()
