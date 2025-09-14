"""
Android Automation Core - Built from scratch
基于 ADB 和 UI 分析的 Android 自动化核心库
"""

import subprocess
import json
import time
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import base64
from PIL import Image
import io


@dataclass
class UIElement:
    """UI 元素数据类"""
    resource_id: str
    text: str
    class_name: str
    bounds: Tuple[int, int, int, int]  # (left, top, right, bottom)
    clickable: bool
    enabled: bool


class AndroidDevice:
    """Android 设备控制器"""

    def __init__(self, device_id: Optional[str] = None):
        """
        初始化 Android 设备连接
        Args:
            device_id: 设备 ID，如果为 None 则使用第一个连接的设备
        """
        self.device_id = device_id or self._get_first_device()
        self._verify_connection()

    def _get_first_device(self) -> str:
        """获取第一个连接的设备"""
        result = self._run_adb_command(['devices'])
        lines = result.strip().split('\n')[1:]  # 跳过标题行

        for line in lines:
            if '\tdevice' in line:
                return line.split('\t')[0]

        raise Exception("未找到连接的 Android 设备")

    def _verify_connection(self):
        """验证设备连接"""
        try:
            result = self._run_adb_command(['shell', 'echo', 'test'])
            if 'test' not in result:
                raise Exception(f"设备 {self.device_id} 连接失败")
            print(f"✅ 设备 {self.device_id} 连接成功")
        except Exception as e:
            raise Exception(f"设备连接验证失败: {e}")

    def _run_adb_command(self, cmd: List[str], timeout: int = 30) -> str:
        """执行 ADB 命令"""
        full_cmd = ['adb']
        if self.device_id:
            full_cmd.extend(['-s', self.device_id])
        full_cmd.extend(cmd)

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exception(f"ADB 命令失败: {' '.join(full_cmd)}\n错误: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception(f"ADB 命令超时: {' '.join(full_cmd)}")

    def tap(self, x: int, y: int):
        """点击坐标"""
        self._run_adb_command(['shell', 'input', 'tap', str(x), str(y)])
        time.sleep(0.5)  # 等待点击生效

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500):
        """滑动操作"""
        self._run_adb_command([
            'shell', 'input', 'swipe',
            str(x1), str(y1), str(x2), str(y2), str(duration)
        ])
        time.sleep(0.5)

    def input_text(self, text: str):
        """输入文本"""
        # 处理中文和特殊字符
        encoded_text = text.replace(' ', '%s')  # 空格需要转义
        self._run_adb_command(['shell', 'input', 'text', encoded_text])
        time.sleep(0.3)

    def press_key(self, keycode: int):
        """按键操作"""
        self._run_adb_command(['shell', 'input', 'keyevent', str(keycode)])
        time.sleep(0.3)

    def start_app(self, package: str, activity: str = None):
        """启动应用"""
        if activity:
            intent = f"{package}/{activity}"
        else:
            intent = package

        self._run_adb_command(['shell', 'am', 'start', '-n', intent])
        time.sleep(2)  # 等待应用启动

    def stop_app(self, package: str):
        """停止应用"""
        self._run_adb_command(['shell', 'am', 'force-stop', package])
        time.sleep(1)

    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        result = self._run_adb_command(['shell', 'wm', 'size'])
        match = re.search(r'(\d+)x(\d+)', result)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 1080, 1920  # 默认值

    def take_screenshot(self, save_path: str = None) -> Image.Image:
        """截屏"""
        result = self._run_adb_command(['shell', 'screencap', '-p'])

        # 处理 Windows 换行符问题
        img_data = result.replace('\r\n', '\n').encode('latin-1')
        img = Image.open(io.BytesIO(img_data))

        if save_path:
            img.save(save_path)

        return img

    def dump_ui_hierarchy(self) -> str:
        """获取 UI 层次结构"""
        # 先生成 UI dump
        self._run_adb_command(['shell', 'uiautomator', 'dump', '/sdcard/ui_dump.xml'])
        # 读取文件内容
        result = self._run_adb_command(['shell', 'cat', '/sdcard/ui_dump.xml'])
        return result


class UIAnalyzer:
    """UI 分析器"""

    def __init__(self, device: AndroidDevice):
        self.device = device

    def find_elements_by_text(self, text: str) -> List[UIElement]:
        """根据文本查找元素"""
        xml_content = self.device.dump_ui_hierarchy()
        return self._parse_elements_from_xml(xml_content, text_filter=text)

    def find_elements_by_resource_id(self, resource_id: str) -> List[UIElement]:
        """根据 resource-id 查找元素"""
        xml_content = self.device.dump_ui_hierarchy()
        return self._parse_elements_from_xml(xml_content, resource_id_filter=resource_id)

    def find_elements_by_class(self, class_name: str) -> List[UIElement]:
        """根据类名查找元素"""
        xml_content = self.device.dump_ui_hierarchy()
        return self._parse_elements_from_xml(xml_content, class_filter=class_name)

    def _parse_elements_from_xml(self, xml_content: str,
                                text_filter: str = None,
                                resource_id_filter: str = None,
                                class_filter: str = None) -> List[UIElement]:
        """从 XML 解析 UI 元素"""
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise Exception(f"UI XML 解析失败: {e}")

        elements = []

        for node in root.iter():
            # 提取属性
            resource_id = node.get('resource-id', '')
            text = node.get('text', '')
            class_name = node.get('class', '')
            bounds_str = node.get('bounds', '')
            clickable = node.get('clickable', 'false') == 'true'
            enabled = node.get('enabled', 'false') == 'true'

            # 解析边界
            bounds = self._parse_bounds(bounds_str)
            if not bounds:
                continue

            # 应用过滤器
            if text_filter and text_filter not in text:
                continue
            if resource_id_filter and resource_id_filter not in resource_id:
                continue
            if class_filter and class_filter not in class_name:
                continue

            element = UIElement(
                resource_id=resource_id,
                text=text,
                class_name=class_name,
                bounds=bounds,
                clickable=clickable,
                enabled=enabled
            )
            elements.append(element)

        return elements

    def _parse_bounds(self, bounds_str: str) -> Optional[Tuple[int, int, int, int]]:
        """解析边界字符串 '[x1,y1][x2,y2]' -> (x1, y1, x2, y2)"""
        if not bounds_str:
            return None

        pattern = r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]'
        match = re.match(pattern, bounds_str)
        if match:
            return tuple(map(int, match.groups()))
        return None

    def get_element_center(self, element: UIElement) -> Tuple[int, int]:
        """获取元素中心坐标"""
        left, top, right, bottom = element.bounds
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        return center_x, center_y


# 使用示例
if __name__ == "__main__":
    print("=== Android 自动化核心测试 ===")

    try:
        # 1. 连接设备
        device = AndroidDevice()
        analyzer = UIAnalyzer(device)

        # 2. 获取设备信息
        width, height = device.get_screen_size()
        print(f"屏幕尺寸: {width} x {height}")

        # 3. 截屏测试
        img = device.take_screenshot("screenshot.png")
        print(f"截屏成功: {img.size}")

        # 4. UI 分析测试
        elements = analyzer.find_elements_by_class("android.widget.TextView")
        print(f"找到 {len(elements)} 个文本元素")

        for i, element in enumerate(elements[:3]):  # 只显示前3个
            print(f"  {i+1}. {element.text} ({element.resource_id})")

        print("✅ 核心功能测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")