import time

from car_actions import Distance_test, frontservo_appointed_detection

def get_distances():
    """
    获取前方、左侧、右侧三个方向的距离
    :return: 返回一个包含三个方向距离的字典
    """
    # 获取左侧距离
    frontservo_appointed_detection(180)
    left_distance = Distance_test()
    time.sleep(1)

    # 获取前方距离
    frontservo_appointed_detection(80)
    front_distance = Distance_test()
    time.sleep(1)

    # 获取右侧距离
    frontservo_appointed_detection(0)
    right_distance = Distance_test()
    time.sleep(1)

    frontservo_appointed_detection(80)
    # 前舵机复位

    # 返回三个方向的距离信息
    distances = {
        'front': front_distance,
        'left': left_distance,
        'right': right_distance
    }
    return distances

if __name__ == "__main__":
    distances = get_distances()

