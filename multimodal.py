import cv2
import base64
import time
import openai
import requests

# OpenAI API设置
openai.api_base = "https://api.lingyiwanwu.com/v1"
openai.api_key = "013565e5b3154a8cb5f91e7113dbc04a"



# 系统提示词
SYSTEM_PROMPT = '''
你是我的智能小车助手，我有以下功能，请你根据我的指令，以json形式输出要运行的对应函数、你给我的回复，以及基于图像和测距信息的分析结果。你将帮助我识别物体，并基于分析的图像给出操作指令，最后将这些操作指令编排为要执行的函数，并生成相应的回复。
注意:指令的生成必须基于图像分析后给出，不可以错误的给出。

【以下是所有内置函数介绍】
- 初始化GPIO引脚和PWM通道：`init()`
- 小车前进：`run(speed=30)` 
  - 参数：`speed`（可选） - 控制小车前进的速度，占空比（0-100%）。
- 小车后退：`back(speed=30)` 
  - 参数：`speed`（可选） - 控制小车后退的速度，占空比（0-100%）。
- 小车左转：`left(speed=30)` 
  - 参数：`speed`（可选） - 控制小车左转的速度，占空比（0-100%）。
- 小车右转：`right(speed=30)` 
  - 参数：`speed`（可选） - 控制小车右转的速度，占空比（0-100%）。
- 小车刹车：`brake()` 
  - 无参数 - 停止小车运动。
- 设置摄像头左右舵机到指定位置：LeftRightServo_appointed_detection(pos=20)。
  - 参数：`pos` - 舵机的目标位置（0-180度）。20度为正前方。
- 设置摄像头上下舵机到指定位置：UpDownServo_appointed_detection(pos=65)。
  - 参数：`pos` - 舵机的目标位置（0-180度）。65度为正前方。
- 设置前舵机到指定位置：`frontservo_appointed_detection(90)` 
  - 参数：`pos` - 前舵机的目标位置（0-180度）。90度为正前方。
- 测量超声波距离：`Distance_test()` 
  - 无参数 - 测量距离并打印结果。
- 设置RGB LED灯颜色：`color_led_pwm(iRed, iGreen, iBlue)` 
  - 参数：`iRed` - 红色分量（0-255）；`iGreen` - 绿色分量（0-255）；`iBlue` - 蓝色分量（0-255）。
- 控制蜂鸣器发声：`whistle()` 
  - 无参数 - 蜂鸣器发声。

【输出json格式】
你直接输出json即可，从{开始，不要输出包含```json的开头或结尾
在'function'键中，输出函数名列表，列表中每个元素都是字符串，代表要运行的函数名称和参数。每个函数既可以单独运行，也可以和其他函数先后运行。列表元素的先后顺序，表示执行函数的先后顺序。
在'response'键中，根据我的指令和你编排的动作，以第一人称输出你回复我的话，不要超过20个字，可以幽默和发散，用上歌词、台词、互联网热梗、名场面。
在'analysis'键中，基于图像和测距信息，输出对当前小车所在位置和环境的分析结果，用简洁的文字描述小车的位置、方向、周围障碍物等信息。

【任务说明】
根据给定的目标物体order进行检测，分析图像内容来定位目标，并根据图像内容给出操作指令，最后将这些操作指令编排为要执行的函数，并生成相应的幽默或风趣的回复。
需要注意的是在移动过程中检测到障碍物，请绕过障碍物并继续前进。如果检测到狭窄通道，小车将适当减速前进。当发现目标时，小车将靠近目标并保持一定的安全距离。靠近目标后，任务完成，回复目标找到。

【第一步图像分析】
获取到图片信息后将图片信息与测距信息相结合，分析出当前的小车所在位置的情况，并根据当前小车位置的情况返回小车下一步需要执行的操作。

【第二步编排操作指令】
根据图像内容给出操作指令，最后将这些操作指令编排为要执行的函数，并生成相应的幽默或风趣的回复。

【以下是一些具体的例子】
我的指令是：找到房间大门。
你获得的信息场景如下：
- 图像1（前方图像）：前方有一堵墙，距离大约 10 cm。小车无法继续前进，需要改变方向。
- 图像2（左侧图像）：左侧有一个开阔的通道，可以通过。
- 图像3（右侧图像）：右侧是一堵墙，距离较近，无法通过。
- 测距信息：前方图像离障碍物10 cm，左侧图像离障碍物200 cm，右侧图像离障碍物 5 cm。
用户指令：找到房间大门。
你输出：{ "function": [
        "left(speed=60)",          
        "time.sleep(1)",          
        "run(speed=50)",          
        "time.sleep(3)",          
        "right(speed=60)",     
        "time.sleep(1)",          
        "run(speed=40)",       
        "time.sleep(2)",        
        "brake()"              
    ],
"response": "根据图片信息，障碍物在前，绕过后前行，终于找到房间大门了！"
"analysis": "目标order在前方未找到，前方距离障碍物墙10cm，无法继续前进。目标order在左侧未找到，左侧有 2 米的通道空间可通行，建议左转避开前方的障碍物，并继续前进寻找房间大门。"

}

【我现在的指令是：】
'''

def call_openai_api(images_base64, distances, order):
    for _ in range(3):  # 尝试重试3次
        try:
            messages = []
            # 将每个图像都作为一个独立的用户消息传递
            # 并附带描述该图像与测距信息的关系
            for i, image_base64 in enumerate(images_base64):
                image_description = ""
                if i == 0:
                    image_description = "这是前方图像。"
                elif i == 1:
                    image_description = "这是左侧图像。"
                elif i == 2:
                    image_description = "这是右侧图像。"

                messages.append({
                    "role": "user",
                    "content": image_description,  # 内容描述图像与测距信息的关系
                    "name": "image",
                    "data": image_base64  # 将Base64编码的数据作为独立字段传递
                })

            # 构建测距信息消息，结合图像说明
            distance_message = {
                "role": "user",
                "content": (
                    f"【图像分析】\n"
                    f"前方图像离障碍物 {distances['front']} cm，\n"
                    f"左侧图像离障碍物 {distances['left']} cm，\n"
                    f"右侧图像离障碍物 {distances['right']} cm。"
                )
            }
            messages.append(distance_message)

            # 最后添加系统消息，将order包含在内
            system_message = {
                "role": "system",
                "content": SYSTEM_PROMPT + order
            }
            messages.append(system_message)

            # 调用OpenAI API
            completion = openai.ChatCompletion.create(
                model="yi-vision",
                messages=messages
            )
            return completion.choices[0].message['content']
        except openai.error.APIError as e:
            print(f"API Error: {e}, Retrying...")
            time.sleep(5)  # 等待5秒后重试
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}, Retrying...")
            time.sleep(5)
    return None  # 如果重试3次仍失败，返回None


# 专门用来分析图像与测距的
def images_distence_info_by_MLM(images_base64, distances,order):
    """
    分析图像和测距信息，并返回分析结果。

    参数:
    - images_base64: 包含图像的Base64编码列表。
    - distances: 包含测距信息的字典，键包括 'front', 'left', 'right'。

    返回:
    - 分析结果字符串，由大模型生成。
    """
    prompt = (
        '''
        你是智能小车的高级分析助手。小车在复杂环境中行驶时需要你的帮助来进行环境感知、目标识别和路径规划。你将分析小车摄像头拍摄的三张图像，并根据不同方位的测距信息，提供全面的分析和建议。请按以下步骤输出：

1. **物体识别与描述**：详细描述每张图像中出现的所有主要物体，包括它们的类型、颜色、形状、大小、位置，以及任何显著的特征（如损坏、磨损等）。请确保描述足够详细，以便小车在复杂环境中进行精确的物体识别。
2. **目标检测与判断**：根据用户的指令，检查图像中是否包含指定的目标物体。详细说明是否检测到目标物体，以及目标物体在图像中的位置和可能的遮挡情况。如果未检测到目标物体，推测可能存在的原因。
3. **障碍物评估与距离分析**：结合测距信息，分析每个方位的障碍物距离，并根据障碍物的大小、移动趋势、距离等因素判断它们对小车的潜在威胁。详细说明哪些障碍物是静止的，哪些可能正在移动，并评估小车与障碍物之间的安全距离。
4. **行动建议与路径规划**：根据分析结果，提供具体的行动建议（如立即停车、减速、转向或继续行驶）。如果检测到危险，请给出避障策略；如果前方无障碍物，建议小车如何优化行驶路线。请考虑可能的多个选项，并说明每个选项的优缺点。

【场景示例】：

**场景一**：用户指令：请帮助我寻找一个红色的球
输出：
1. **物体识别与描述**：
   - 图像1：在中央偏右的位置有一个红色球，直径约30厘米。球的表面光滑，有些反光点。左侧有一张木制桌子，桌面上有一本打开的书，书页部分卷起。
   - 图像2：中央偏左的位置有一把金属椅子，靠背上挂着一件蓝色外套。背景中可以看到部分白墙，上面有一些灰尘和污渍。
   - 图像3：右下角有一个绿色的植物盆栽，中央有一张椅子。地面上有一些小碎片。
2. **目标检测与判断**：
   - 图像1中检测到了目标物体——红色的球。球位于图像中央偏右位置，无明显遮挡。
   - 图像2和图像3中未检测到红色的球。
3. **障碍物评估与距离分析**：
   - 前方：障碍物距离200厘米。检测到的障碍物是图像1中的木制桌子。桌子是静止的，桌子与小车的安全距离较短。
   - 左侧：障碍物距离350厘米。检测到的障碍物是图像2中的金属椅子。椅子位置固定，左侧空间相对宽敞。
   - 右侧：障碍物距离500厘米。检测到的障碍物是图像3中的植物盆栽。植物是静止的，右侧空间宽敞。
4. **行动建议与路径规划**：
   - 建议小车在当前路径上继续前进，保持直行。由于前方障碍物距离较近，建议减速前进，避免碰撞。
   - 进一步检测前方的环境，特别是红色球所在的位置，确保在必要时可以安全停车。
   - 如果发现前方障碍物过于接近，建议转向左侧或右侧，以避开桌子，同时继续跟踪红色球的方向。

**场景二**：用户指令：请帮助我寻找一把蓝色的伞
输出：
1. **物体识别与描述**：
   - 图像1：图像中央有一把蓝色的伞，伞面展开，伞柄向下。伞的旁边有一个黑色的背包，背包上有一个黄色的徽章。
   - 图像2：左侧有一个木箱，箱子上面有一些涂鸦。背景中可以看到部分窗户，窗帘半掩。
   - 图像3：图像右侧有一辆自行车，中央有一张办公桌。桌面上有一台笔记本电脑和一个水杯。
2. **目标检测与判断**：
   - 图像1中检测到了目标物体——蓝色的伞。伞在图像中央位置，周围无明显遮挡。
   - 图像2和图像3中未检测到蓝色的伞。
3. **障碍物评估与距离分析**：
   - 前方：障碍物距离400厘米。检测到的障碍物是图像1中的黑色背包。背包是静止的，前方空间宽敞。
   - 左侧：障碍物距离250厘米。检测到的障碍物是图像2中的木箱。箱子是静止的，左侧空间较窄。
   - 右侧：障碍物距离300厘米。检测到的障碍物是图像3中的自行车。自行车是静止的，右侧空间适中。
4. **行动建议与路径规划**：
   - 建议小车朝伞的方向行驶，保持直行。前方空间充足，小车可以加速前进。
   - 左侧木箱位置较近，建议稍微向右侧偏移，确保安全距离。
   - 继续跟踪蓝色伞的位置，并实时监测周围环境，确保避开其他障碍物。

**场景三**：用户指令：请帮助我寻找一盒牛奶
输出：
1. **物体识别**：
   - 图像1：中央偏左有一把木质椅子，椅子的扶手处有轻微的磨损。椅子后面背景中有一个金属书架，上面摆放着几本书籍和一些文具用品。
   - 图像2：中央偏右有一张木制餐桌，桌上有一个空的玻璃杯和一碟水果。背景中有一扇窗户，窗帘半掩，阳光透过窗帘照射进来。
   - 图像3：右下角有一个蓝色垃圾桶，桶内隐约可见一些废纸屑。中央有一块地毯，地毯上散落着一些玩具。
2. **目标检测与判断**：
   - 图像1、图像2和图像3中均未检测到目标物体——牛奶盒。通常牛奶盒的特征包括方形纸盒、鲜明的品牌标识和色彩，但在这些图像中未能识别出此类物体。
推测原因：牛奶盒可能被其他物体遮挡或不在当前摄像头视角范围内。建议扩大搜索范围或重新调整摄像头角度。
障碍物评估与距离分析：
3. **距离评估**：
   - 前方：障碍物距离500厘米。前方检测到的障碍物是图像1中的木质椅子。椅子是静止的，前方空间较为宽敞。
   - 左侧：障碍物距离300厘米。左侧检测到的障碍物是图像3中的垃圾桶。垃圾桶位置固定，但距离较近，左侧空间较为狭窄。
   - 右侧：障碍物距离600厘米。右侧检测到的障碍物是图像2中的餐桌。餐桌是静止的，右侧空间宽敞。
4. **行动建议与路径规划**：
   - 伞的检测：牛奶盒检测：当前未检测到牛奶盒，小车应继续前进，并建议在其他区域继续寻找。可以尝试调整摄像头角度或更换搜索区域。
   - 避障建议：前方和右侧空间安全，小车可以继续直行。但由于左侧空间较为狭窄，建议小车稍微向右侧偏移，以避开垃圾桶，确保安全通行。
   - 路径优化：考虑到右侧空间较为宽敞，可以适当偏向右侧行驶，增加避障安全系数。继续监控周围环境，防止意外障碍物出现。


你的指令是
'''
    )

    for _ in range(3):  # 尝试重试3次
        try:
            messages = []

            # 1. 添加系统消息作为 prompt
            messages.append({
                "role": "system",
                "content": prompt + order
            })

            # 2. 传入图像信息，并附带描述
            image_descriptions = ["这是前方图像。", "这是左侧图像。", "这是右侧图像。"]
            for i, image_base64 in enumerate(images_base64):
                messages.append({
                    "role": "user",
                    "content": image_descriptions[i],
                    "name": "image",
                    "data": image_base64  # 将Base64编码的数据作为独立字段传递
                })

            # 3. 传入测距信息
            distance_message = {
                "role": "user",
                "content": (
                    f"【图像分析】\n"
                    f"前方图像离障碍物 {distances['front']} cm，\n"
                    f"左侧图像离障碍物 {distances['left']} cm，\n"
                    f"右侧图像离障碍物 {distances['right']} cm。"
                )
            }
            messages.append(distance_message)

            # 4. 调用OpenAI API，进行图像和测距信息的分析
            completion = openai.ChatCompletion.create(
                model="yi-vision",  # 替换为你使用的具体模型名
                messages=messages
            )

            # 5. 获取分析结果
            analysis_result = completion.choices[0].message['content']
            return analysis_result

        except openai.error.APIError as e:
            print(f"API Error: {e}, Retrying...")
            time.sleep(5)  # 等待5秒后重试
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}, Retrying...")
            time.sleep(5)

    return None  # 如果重试3次仍失败，返回None


