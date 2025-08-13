import cv2
import numpy as np
import os
import time
from video_processor import VideoProcessor
from region_selector import RegionSelector


def create_test_video_with_changes(filename="test_video.mp4", duration=10, fps=30):
    """
    创建带有明显变化的测试视频
    :param filename: 输出文件名
    :param duration: 视频持续时间(秒)
    :param fps: 帧率
    :return: 视频文件路径
    """
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    # 创建背景
    background = np.ones((height, width, 3), dtype=np.uint8) * 240  # 浅灰色背景

    # 创建一个移动的矩形
    rect_width, rect_height = 200, 150
    x, y = 100, 100
    dx, dy = 5, 3

    total_frames = duration * fps
    change_frame = total_frames // 2  # 中间帧发生变化

    for i in range(total_frames):
        # 复制背景
        frame = background.copy()

        # 绘制移动的矩形
        cv2.rectangle(frame, (x, y), (x + rect_width, y + rect_height), (0, 0, 255), -1)

        # 在中间帧改变矩形颜色和大小
        if i == change_frame:
            rect_width, rect_height = 250, 180
            dx, dy = 7, 4
            cv2.rectangle(frame, (x, y), (x + rect_width, y + rect_height), (0, 255, 0), -1)
            # 添加一些随机噪点
            noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
            frame = cv2.add(frame, noise)

        # 更新位置
        x += dx
        y += dy

        # 边界检查
        if x < 0 or x + rect_width > width:
            dx = -dx
        if y < 0 or y + rect_height > height:
            dy = -dy

        # 写入帧
        out.write(frame)

    out.release()
    print(f"测试视频已创建: {filename}")
    return filename


def test_video_change_detector():
    """
    测试视频变化检测工具
    """
    print("===== 视频变化检测工具测试 =====")

    # 创建测试视频
    test_video_path = create_test_video_with_changes()

    # 读取视频第一帧用于区域选择
    cap = cv2.VideoCapture(test_video_path)
    ret, first_frame = cap.read()
    cap.release()

    if not ret:
        print("无法读取测试视频的第一帧")
        return

    # 选择感兴趣区域
    selector = RegionSelector()
    region = selector.select_region(first_frame)
    print(f"选择的区域: x={region[0]}, y={region[1]}, w={region[2]}, h={region[3]}")

    # 创建视频处理器
    processor = VideoProcessor(sensitivity=25.0, min_scene_len=5)
    processor.set_region(region)
    # 降低变化阈值以提高灵敏度
    processor.change_threshold = 100

    # 处理视频
    try:
        start_time = time.time()
        events = processor.process_video(test_video_path)
        end_time = time.time()

        print(f"处理完成，检测到 {len(events)} 个变化事件，耗时: {end_time - start_time:.2f} 秒")
    except Exception as e:
        print(f"处理视频时出错: {e}")
        return

    # 生成测试报告
    print("\n===== 测试报告 =====")
    print(f"测试视频: {test_video_path}")
    print(f"感兴趣区域: x={region[0]}, y={region[1]}, w={region[2]}, h={region[3]}")
    print(f"检测到 {len(events)} 个变化事件")
    print(f"检测结果保存在: screenshots 目录")
    print("测试完成")


if __name__ == "__main__":
    test_video_change_detector()
