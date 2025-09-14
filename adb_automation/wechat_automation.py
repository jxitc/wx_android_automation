"""
WeChat Android Automation - Built from scratch
微信 Android 自动化 - 从零构建
"""

import time
import cv2
import numpy as np
from PIL import Image
from typing import List, Optional, Tuple
from .core import AndroidDevice, UIAnalyzer, UIElement


class WeChatAutomation:
    """微信自动化控制器"""

    # 微信应用信息
    WECHAT_PACKAGE = "com.tencent.mm"
    WECHAT_MAIN_ACTIVITY = "com.tencent.mm.ui.LauncherUI"

    # 常用的 resource-id (需要根据实际微信版本调整)
    SEARCH_BOX_ID = "com.tencent.mm:id/f8x"
    CHAT_INPUT_ID = "com.tencent.mm:id/al_"
    SEND_BUTTON_ID = "com.tencent.mm:id/anv"
    CONTACT_LIST_ID = "com.tencent.mm:id/e3k"

    def __init__(self, device_id: Optional[str] = None):
        self.device = AndroidDevice(device_id)
        self.analyzer = UIAnalyzer(self.device)
        self.is_wechat_running = False

    def start_wechat(self):
        """启动微信"""
        print("🚀 启动微信...")
        self.device.start_app(self.WECHAT_PACKAGE, self.WECHAT_MAIN_ACTIVITY)
        self.is_wechat_running = True

        # 等待微信完全加载
        time.sleep(3)
        self._wait_for_main_screen()

    def _wait_for_main_screen(self, timeout: int = 10):
        """等待主界面加载"""
        print("⏳ 等待微信主界面加载...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # 查找特征元素，如 "微信" 标题或底部导航
                elements = self.analyzer.find_elements_by_text("微信")
                if elements:
                    print("✅ 微信主界面已加载")
                    return

                # 或查找底部导航栏
                nav_elements = self.analyzer.find_elements_by_text("通讯录")
                if nav_elements:
                    print("✅ 微信主界面已加载")
                    return

            except Exception as e:
                print(f"检查主界面状态时出错: {e}")

            time.sleep(1)

        raise Exception("微信主界面加载超时")

    def find_contact(self, contact_name: str) -> bool:
        """查找联系人"""
        print(f"🔍 查找联系人: {contact_name}")

        try:
            # 方法1: 直接在聊天列表中查找
            contact_elements = self.analyzer.find_elements_by_text(contact_name)
            if contact_elements:
                # 点击联系人
                contact = contact_elements[0]
                center_x, center_y = self.analyzer.get_element_center(contact)
                self.device.tap(center_x, center_y)
                print(f"✅ 找到并点击联系人: {contact_name}")
                time.sleep(2)
                return True

            # 方法2: 使用搜索功能
            return self._search_contact(contact_name)

        except Exception as e:
            print(f"查找联系人失败: {e}")
            return False

    def _search_contact(self, contact_name: str) -> bool:
        """通过搜索查找联系人"""
        print(f"🔍 通过搜索查找: {contact_name}")

        try:
            # 查找搜索按钮或搜索框
            search_elements = self.analyzer.find_elements_by_resource_id(self.SEARCH_BOX_ID)
            if not search_elements:
                # 尝试通过文本查找搜索
                search_elements = self.analyzer.find_elements_by_text("搜索")

            if search_elements:
                # 点击搜索框
                search_box = search_elements[0]
                center_x, center_y = self.analyzer.get_element_center(search_box)
                self.device.tap(center_x, center_y)
                time.sleep(1)

                # 输入联系人名称
                self.device.input_text(contact_name)
                time.sleep(2)

                # 查找搜索结果中的联系人
                result_elements = self.analyzer.find_elements_by_text(contact_name)
                if result_elements:
                    # 点击第一个结果
                    result = result_elements[0]
                    center_x, center_y = self.analyzer.get_element_center(result)
                    self.device.tap(center_x, center_y)
                    print(f"✅ 通过搜索找到联系人: {contact_name}")
                    time.sleep(2)
                    return True

        except Exception as e:
            print(f"搜索联系人失败: {e}")

        return False

    def send_message(self, message: str) -> bool:
        """发送消息"""
        print(f"📤 发送消息: {message}")

        try:
            # 查找输入框
            input_elements = self.analyzer.find_elements_by_resource_id(self.CHAT_INPUT_ID)
            if not input_elements:
                # 尝试通过类名查找
                input_elements = self.analyzer.find_elements_by_class("android.widget.EditText")

            if not input_elements:
                print("❌ 未找到消息输入框")
                return False

            # 点击输入框
            input_box = input_elements[0]
            center_x, center_y = self.analyzer.get_element_center(input_box)
            self.device.tap(center_x, center_y)
            time.sleep(0.5)

            # 输入消息
            self.device.input_text(message)
            time.sleep(1)

            # 查找发送按钮
            send_elements = self.analyzer.find_elements_by_resource_id(self.SEND_BUTTON_ID)
            if not send_elements:
                # 尝试通过文本查找
                send_elements = self.analyzer.find_elements_by_text("发送")

            if send_elements:
                # 点击发送按钮
                send_button = send_elements[0]
                center_x, center_y = self.analyzer.get_element_center(send_button)
                self.device.tap(center_x, center_y)
                print(f"✅ 消息发送成功: {message}")
                time.sleep(1)
                return True
            else:
                # 如果找不到发送按钮，尝试按回车键
                self.device.press_key(66)  # KEYCODE_ENTER
                print(f"✅ 通过回车键发送消息: {message}")
                time.sleep(1)
                return True

        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def get_latest_messages(self, count: int = 5) -> List[str]:
        """获取最新消息"""
        print(f"📥 获取最新 {count} 条消息...")

        try:
            # 查找消息元素
            message_elements = self.analyzer.find_elements_by_class("android.widget.TextView")

            # 过滤出可能是消息内容的元素
            messages = []
            for element in message_elements:
                if (element.text and
                    len(element.text.strip()) > 0 and
                    element.text not in ["微信", "通讯录", "发现", "我", "发送"]):
                    messages.append(element.text.strip())

            # 返回最新的几条消息
            return messages[-count:] if messages else []

        except Exception as e:
            print(f"获取消息失败: {e}")
            return []

    def send_message_to_contact(self, contact_name: str, message: str) -> bool:
        """向指定联系人发送消息"""
        print(f"📱 向 {contact_name} 发送消息: {message}")

        if not self.is_wechat_running:
            self.start_wechat()

        # 查找并点击联系人
        if self.find_contact(contact_name):
            # 发送消息
            return self.send_message(message)
        else:
            print(f"❌ 未找到联系人: {contact_name}")
            return False

    def take_screenshot_with_annotation(self, save_path: str = "wechat_screenshot.png"):
        """截屏并标注 UI 元素"""
        print(f"📸 截屏并分析 UI 元素...")

        # 截屏
        img = self.device.take_screenshot()

        # 转换为 OpenCV 格式
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # 获取所有可点击元素
        try:
            xml_content = self.device.dump_ui_hierarchy()
            all_elements = self.analyzer._parse_elements_from_xml(xml_content)

            # 在图片上标注元素
            for element in all_elements:
                if element.clickable and element.bounds:
                    left, top, right, bottom = element.bounds

                    # 画矩形框
                    cv2.rectangle(cv_img, (left, top), (right, bottom), (0, 255, 0), 2)

                    # 添加文本标签
                    label = element.text or element.resource_id.split(':')[-1] if element.resource_id else "clickable"
                    cv2.putText(cv_img, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        except Exception as e:
            print(f"UI 分析失败: {e}")

        # 保存标注后的图片
        cv2.imwrite(save_path, cv_img)
        print(f"✅ 截屏已保存: {save_path}")

        return save_path


# 使用示例
if __name__ == "__main__":
    print("=== 微信自动化测试 ===")

    try:
        # 创建微信自动化实例
        wechat = WeChatAutomation()

        # 启动微信
        wechat.start_wechat()

        # 截屏分析当前界面
        wechat.take_screenshot_with_annotation("current_wechat_ui.png")

        # 发送测试消息
        success = wechat.send_message_to_contact("测试联系人", "Hello from Android automation!")

        if success:
            print("✅ 消息发送成功")
        else:
            print("❌ 消息发送失败")

        # 获取最新消息
        messages = wechat.get_latest_messages(3)
        print(f"最新消息: {messages}")

    except Exception as e:
        print(f"❌ 自动化测试失败: {e}")