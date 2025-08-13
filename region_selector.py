import cv2
import numpy as np
import platform
import ctypes

def get_screen_resolution():
    """
    获取屏幕分辨率
    :return: (width, height) 屏幕分辨率
    """
    if platform.system() == "Windows":
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    elif platform.system() == "Linux":
        import subprocess
        output = subprocess.Popen(['xrandr'], stdout=subprocess.PIPE).communicate()[0]
        output = output.decode('utf-8')
        for line in output.split('\n'):
            if 'current' in line:
                width = int(line.split('current')[1].split(',')[0].split('x')[0].strip())
                height = int(line.split('current')[1].split(',')[0].split('x')[1].strip())
                return width, height
    elif platform.system() == "Darwin":  # macOS
        import subprocess
        output = subprocess.Popen(['system_profiler', 'SPDisplaysDataType'], stdout=subprocess.PIPE).communicate()[0]
        output = output.decode('utf-8')
        for line in output.split('\n'):
            if 'Resolution' in line:
                width = int(line.split('Resolution:')[1].split('x')[0].strip())
                height = int(line.split('Resolution:')[1].split('x')[1].strip())
                return width, height
    # 默认返回一个常见分辨率
    return 1920, 1080

class RegionSelector:
    def __init__(self):
        """
        初始化区域选择器
        """
        self.region = None
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.frame = None
        self.original_frame = None
        self.scale_factor = 1.0
        # 修改窗口标题，确保中文能正确显示
        self.window_name = "Select Region of Interest (Drag to draw, Enter to confirm)"

    def select_region(self, frame):
        """
        选择感兴趣区域
        :param frame: 视频帧
        :return: 选择的区域 (x, y, w, h) 在原始视频帧中的坐标
        """
        self.original_frame = frame.copy()
        self.frame = frame.copy()
        
        # 获取屏幕分辨率
        screen_width, screen_height = get_screen_resolution()
        
        # 计算缩放因子，确保视频帧适应屏幕
        frame_height, frame_width = self.frame.shape[:2]
        width_ratio = screen_width / frame_width
        height_ratio = screen_height / frame_height
        # 留一些边距
        self.scale_factor = min(width_ratio, height_ratio) * 0.9
        
        # 如果需要缩放
        if self.scale_factor < 1.0:
            new_width = int(frame_width * self.scale_factor)
            new_height = int(frame_height * self.scale_factor)
            self.frame = cv2.resize(self.frame, (new_width, new_height))
        
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._draw_rectangle)

        while True:
            # 显示当前帧和绘制的矩形
            display_frame = self.frame.copy()
            if self.region is not None:
                x, y, w, h = self.region
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.imshow(self.window_name, display_frame)

            # 等待按键
            key = cv2.waitKey(1) & 0xFF

            # 按Enter键确认选择
            if key == 13:  # Enter键
                break
            # 按r键重置选择
            elif key == ord('r'):
                self.region = None
                self.frame = self.original_frame.copy()
                if self.scale_factor < 1.0:
                    new_width = int(self.original_frame.shape[1] * self.scale_factor)
                    new_height = int(self.original_frame.shape[0] * self.scale_factor)
                    self.frame = cv2.resize(self.frame, (new_width, new_height))
            # 按q键退出
            elif key == ord('q'):
                cv2.destroyAllWindows()
                return None

        cv2.destroyAllWindows()
        
        # 如果进行了缩放，将选择的区域映射回原始视频帧尺寸
        if self.region is not None and self.scale_factor < 1.0:
            x, y, w, h = self.region
            x = int(x / self.scale_factor)
            y = int(y / self.scale_factor)
            w = int(w / self.scale_factor)
            h = int(h / self.scale_factor)
            return (x, y, w, h)
        
        return self.region

    def _draw_rectangle(self, event, x, y, flags, param):
        """
        鼠标回调函数，用于绘制矩形
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                # 绘制矩形
                temp_frame = self.frame.copy()
                cv2.rectangle(temp_frame, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
                cv2.imshow(self.window_name, temp_frame)

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            # 确保宽度和高度为正数
            x1 = min(self.ix, x)
            y1 = min(self.iy, y)
            x2 = max(self.ix, x)
            y2 = max(self.iy, y)
            self.region = (x1, y1, x2-x1, y2-y1)

if __name__ == "__main__":
    # 示例用法
    # 创建一个大尺寸的测试图像
    test_image = np.zeros((1500, 2500, 3), dtype=np.uint8) + 255  # 白色背景
    cv2.putText(test_image, "Drag to select region of interest", (100, 200), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(test_image, "Press Enter to confirm, r to reset, q to quit", (100, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    selector = RegionSelector()
    region = selector.select_region(test_image)

    if region is not None:
        x, y, w, h = region
        print(f"Selected region: x={x}, y={y}, w={w}, h={h}")
        # 在原图上绘制选择的区域
        cv2.rectangle(test_image, (x, y), (x+w, y+h), (0, 0, 255), 2)
        # 缩放图像以适应屏幕显示
        screen_width, screen_height = get_screen_resolution()
        height, width = test_image.shape[:2]
        width_ratio = screen_width / width
        height_ratio = screen_height / height
        scale_factor = min(width_ratio, height_ratio) * 0.9
        if scale_factor < 1.0:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            test_image = cv2.resize(test_image, (new_width, new_height))
        cv2.imshow("Selected Region", test_image)
        cv2.waitKey(0)
    else:
        print("No region selected")

    cv2.destroyAllWindows()
