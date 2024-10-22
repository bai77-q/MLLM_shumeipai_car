from car_actions import *  # 导入car_actions.py中的所有函数
from camera import *  # 导入camera.py中的所有函数
# from voice_recognition import *  # 导入voice_recognition.py中的所有函数
from utils_llmPrompts import *  # 导入nlp_processing.py中的所有函数
from multimodal import *  # 导入multimodal_processing.py中的所有函数
from utils_llm import *
# from utils_tts import *
from get_distences import *
from get_image import *
import time  # 导入time模块用于添加延时

def agent_play():
    '''
    主函数，语音控制机械臂智能体编排动作
    '''
    # 小车初始化
    init()
    # 输入指令
    order = input('请输入指令')

    while True:

        # images = analyze_image()
        images = get_image()
        distances=get_distances()

       # 只看图像加测距的info信息
        info = images_distence_info_by_MLM(images,distances,order)
        # agent_plan_output = eval(call_openai_api()
        print(info)
        break

        # 智能体Agent编排动作。多模态大模型
        # agent_plan_output = eval(call_openai_api(images,distances,order))

        # 智能体Agent编排动作。普通大模型
        # agent_plan_output = eval(agent_plan(order))

        print('智能体编排动作如下\n', agent_plan_output)

        # 执行智能体编排的每个函数
        for each in agent_plan_output['function']:  # 运行智能体规划编排的每个函数
            try:
                print('开始执行动作:', each)
                eval(each)  # 执行每个函数
                time.sleep(0.5)  # 每个任务之间添加0.5秒的缓冲时间
            except Exception as e:
                print(f'执行动作 {each} 时发生错误: {e}')
        brake()  # 每次分析完，小车必须停止

        plan_ok = input('动作执行完成，是否继续？按c继续输入新指令，按q退出\n')
        if plan_ok == 'q':
            print('程序退出')
            break
        elif plan_ok == 'c':
            print('继续执行')
            continue
        else:
            print('无效输入，程序结束')
            break



# 语音输入等混合操作，后面再调用，因为用的api没充钱
    # 输入指令
    # start_record_ok = input('是否开启录音，输入数字录音指定时长，按k打字输入，按c输入默认指令\n')
    # if str.isnumeric(start_record_ok):
    #     # DURATION = int(start_record_ok)
    #     # record(DURATION=DURATION)  # 录音
    #     # order = speech_recognition()  # 语音识别
    # elif start_record_ok == 'k':
    #     order = input('请输入指令')
    # elif start_record_ok == 'c':
    #     order = '亮红灯，亮黄灯，测距，摄像头向左转90度'
    # else:
    #     print('无指令，退出')
    #     # exit()
    #     raise NameError('无指令，退出')

    # 智能体Agent编排动作
    # agent_plan_output = eval(agent_plan(order))
    #
    # print('智能体编排动作如下\n', agent_plan_output)
    # plan_ok = input('是否继续？按c继续，按q退出')
    # plan_ok = 'c'
    # if plan_ok == 'c':
    #     response = agent_plan_output['response']  # 获取机器人想对我说的话
    #     print('开始语音合成')
    #     tts(response)  # 语音合成，导出wav音频文件
    #     play_wav('temp/tts.wav')  # 播放语音合成音频文件
    #     for each in agent_plan_output['function']:  # 运行智能体规划编排的每个函数
    #         print('开始执行动作', each)
    #         eval(each)
    # elif plan_ok == 'q':
    #     # exit()
    #     raise NameError('按q退出')


# agent_play()
if __name__ == '__main__':
    agent_play()

