"""
Image-based UI Element Recognition
基于图像识别的 UI 元素查找
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple, Optional
import os


class ImageMatcher:
    """图像匹配器 - 用于在屏幕截图中查找UI元素"""

    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold

    def find_element_by_template(self, screenshot: Image.Image,
                                template_path: str) -> Optional[Tuple[int, int, int, int]]:
        """
        使用模板匹配在截图中查找元素

        Args:
            screenshot: 屏幕截图
            template_path: 模板图片路径

        Returns:
            元素边界 (left, top, right, bottom) 或 None
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板图片不存在: {template_path}")

        # 转换为 OpenCV 格式
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path)

        if template is None:
            raise ValueError(f"无法读取模板图片: {template_path}")

        # 获取模板尺寸
        template_height, template_width = template.shape[:2]

        # 模板匹配
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

        # 查找最佳匹配
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.confidence_threshold:
            # 计算边界
            left = max_loc[0]
            top = max_loc[1]
            right = left + template_width
            bottom = top + template_height

            return (left, top, right, bottom)

        return None

    def find_all_elements_by_template(self, screenshot: Image.Image,
                                     template_path: str) -> List[Tuple[int, int, int, int]]:
        """查找所有匹配的元素"""
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板图片不存在: {template_path}")

        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path)
        template_height, template_width = template.shape[:2]

        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

        # 查找所有高于阈值的匹配
        locations = np.where(result >= self.confidence_threshold)

        elements = []
        for pt in zip(*locations[::-1]):  # OpenCV 返回的是 (y, x)，需要转换
            left = pt[0]
            top = pt[1]
            right = left + template_width
            bottom = top + template_height
            elements.append((left, top, right, bottom))

        # 去除重叠的检测结果
        return self._remove_overlapping_boxes(elements)

    def _remove_overlapping_boxes(self, boxes: List[Tuple[int, int, int, int]],
                                 overlap_threshold: float = 0.5) -> List[Tuple[int, int, int, int]]:
        """移除重叠的检测框"""
        if not boxes:
            return []

        # 按置信度排序（这里简化处理，实际可以加入置信度信息）
        boxes = sorted(boxes, key=lambda x: (x[0], x[1]))

        filtered_boxes = []
        for box in boxes:
            is_overlapping = False
            for existing_box in filtered_boxes:
                if self._calculate_overlap(box, existing_box) > overlap_threshold:
                    is_overlapping = True
                    break

            if not is_overlapping:
                filtered_boxes.append(box)

        return filtered_boxes

    def _calculate_overlap(self, box1: Tuple[int, int, int, int],
                          box2: Tuple[int, int, int, int]) -> float:
        """计算两个框的重叠比例"""
        x1_left, y1_top, x1_right, y1_bottom = box1
        x2_left, y2_top, x2_right, y2_bottom = box2

        # 计算交集
        intersection_left = max(x1_left, x2_left)
        intersection_top = max(y1_top, y2_top)
        intersection_right = min(x1_right, x2_right)
        intersection_bottom = min(y1_bottom, y2_bottom)

        if intersection_right <= intersection_left or intersection_bottom <= intersection_top:
            return 0.0

        intersection_area = (intersection_right - intersection_left) * (intersection_bottom - intersection_top)

        # 计算并集
        box1_area = (x1_right - x1_left) * (y1_bottom - y1_top)
        box2_area = (x2_right - x2_left) * (y2_bottom - y2_top)
        union_area = box1_area + box2_area - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0

    def find_text_by_ocr(self, screenshot: Image.Image, target_text: str) -> List[Tuple[int, int, int, int]]:
        """
        使用 OCR 查找文本元素
        注意: 需要安装 pytesseract 和 tesseract
        """
        try:
            import pytesseract
        except ImportError:
            print("警告: pytesseract 未安装，无法使用 OCR 功能")
            return []

        # 转换为灰度图像
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)

        # 使用 OCR 检测文本
        try:
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, lang='chi_sim+eng')

            elements = []
            for i, text in enumerate(data['text']):
                if target_text in text and int(data['conf'][i]) > 50:  # 置信度大于50
                    left = data['left'][i]
                    top = data['top'][i]
                    width = data['width'][i]
                    height = data['height'][i]

                    elements.append((left, top, left + width, top + height))

            return elements

        except Exception as e:
            print(f"OCR 处理失败: {e}")
            return []


class WeChatImageAutomation:
    """基于图像识别的微信自动化"""

    def __init__(self, device, templates_dir: str = "templates"):
        from .core import AndroidDevice
        self.device = device
        self.matcher = ImageMatcher()
        self.templates_dir = templates_dir

        # 创建模板目录
        os.makedirs(templates_dir, exist_ok=True)

    def click_element_by_image(self, template_name: str) -> bool:
        """通过图像模板点击元素"""
        template_path = os.path.join(self.templates_dir, f"{template_name}.png")

        if not os.path.exists(template_path):
            print(f"警告: 模板图片不存在 {template_path}")
            return False

        # 截屏
        screenshot = self.device.take_screenshot()

        # 查找元素
        element_bounds = self.matcher.find_element_by_template(screenshot, template_path)

        if element_bounds:
            left, top, right, bottom = element_bounds
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2

            # 点击元素
            self.device.tap(center_x, center_y)
            print(f"✅ 通过图像模板点击: {template_name}")
            return True
        else:
            print(f"❌ 未找到图像模板: {template_name}")
            return False

    def wait_for_element_by_image(self, template_name: str, timeout: int = 10) -> bool:
        """等待图像元素出现"""
        template_path = os.path.join(self.templates_dir, f"{template_name}.png")

        if not os.path.exists(template_path):
            print(f"警告: 模板图片不存在 {template_path}")
            return False

        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            screenshot = self.device.take_screenshot()
            element_bounds = self.matcher.find_element_by_template(screenshot, template_path)

            if element_bounds:
                print(f"✅ 图像元素已出现: {template_name}")
                return True

            time.sleep(1)

        print(f"❌ 等待图像元素超时: {template_name}")
        return False

    def create_template(self, template_name: str, bounds: Tuple[int, int, int, int]):
        """从当前屏幕创建模板图片"""
        screenshot = self.device.take_screenshot()

        # 裁剪指定区域
        left, top, right, bottom = bounds
        template_img = screenshot.crop((left, top, right, bottom))

        # 保存模板
        template_path = os.path.join(self.templates_dir, f"{template_name}.png")
        template_img.save(template_path)

        print(f"✅ 模板已创建: {template_path}")
        return template_path

    def analyze_current_screen(self, save_path: str = "screen_analysis.png"):
        """分析当前屏幕并保存标注图片"""
        screenshot = self.device.take_screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 使用边缘检测找到可能的UI元素
        gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 绘制轮廓和边界框
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 50000:  # 过滤太小或太大的区域
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(screenshot_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(screenshot_cv, f"Area:{int(area)}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 保存分析结果
        cv2.imwrite(save_path, screenshot_cv)
        print(f"✅ 屏幕分析完成: {save_path}")

        return save_path


# 使用示例
if __name__ == "__main__":
    print("=== 图像识别自动化测试 ===")

    try:
        from .core import AndroidDevice

        # 创建设备和图像自动化实例
        device = AndroidDevice()
        image_auto = WeChatImageAutomation(device)

        # 分析当前屏幕
        image_auto.analyze_current_screen("current_screen_analysis.png")

        # 示例: 创建发送按钮模板
        # 假设发送按钮在屏幕的某个位置
        # image_auto.create_template("send_button", (900, 600, 1000, 700))

        # 示例: 通过图像点击发送按钮
        # image_auto.click_element_by_image("send_button")

        print("✅ 图像识别测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")