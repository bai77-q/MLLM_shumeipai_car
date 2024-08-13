from car_actions import *

def control_all_servos(left_right_pos=90, up_down_pos=90, front_pos=90):
    """
    控制左右、上下和前舵机旋转到指定位置
    :param left_right_pos: 左右舵机的目标位置角度（0-180度）
    :param up_down_pos: 上下舵机的目标位置角度（0-180度）
    :param front_pos: 前舵机的目标位置角度（0-180度）
    """
    LeftRightServo_appointed_detection(left_right_pos)
    UpDownServo_appointed_detection(up_down_pos)
    frontservo_appointed_detection(front_pos)

def main():
    """
    程序的主函数，负责执行舵机控制的逻辑。
    """
    init()

    while True:
        try:
            # 用户输入舵机的角度
            left_right_pos = int(input("请输入左右舵机的角度 (0-180)，或输入-1退出: "))
            if left_right_pos == -1:
                print("程序退出。")
                break

            up_down_pos = int(input("请输入上下舵机的角度 (0-180)，或输入-1退出: "))
            if up_down_pos == -1:
                print("程序退出。")
                break

            front_pos = int(input("请输入前舵机的角度 (0-180)，或输入-1退出: "))
            if front_pos == -1:
                print("程序退出。")
                break

            # 控制三个舵机到指定的位置
            control_all_servos(left_right_pos, up_down_pos, front_pos)

        except ValueError as e:
            print(f"输入无效: {e}")

if __name__ == "__main__":
    main()
