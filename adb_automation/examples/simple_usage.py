"""
Simple Usage Examples
简单使用示例
"""

import sys
import os

# 添加父目录到路径以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from android_automation import WeChatAutomation, AndroidDevice


def basic_messaging_example():
    """基础消息发送示例"""
    print("=== 基础消息发送示例 ===")

    try:
        # 1. 创建微信自动化实例
        wechat = WeChatAutomation()

        # 2. 启动微信
        wechat.start_wechat()

        # 3. 发送消息给指定联系人
        contact_name = "测试联系人"  # 替换为实际联系人名称
        message = "Hello from Android automation!"

        success = wechat.send_message_to_contact(contact_name, message)

        if success:
            print("✅ 消息发送成功")

            # 4. 获取最新消息
            messages = wechat.get_latest_messages(3)
            print(f"最新消息: {messages}")
        else:
            print("❌ 消息发送失败")

    except Exception as e:
        print(f"示例执行失败: {e}")


def device_info_example():
    """设备信息获取示例"""
    print("=== 设备信息获取示例 ===")

    try:
        # 连接设备
        device = AndroidDevice()

        # 获取屏幕尺寸
        width, height = device.get_screen_size()
        print(f"屏幕尺寸: {width} x {height}")

        # 截屏
        screenshot = device.take_screenshot("device_screenshot.png")
        print(f"截屏成功: {screenshot.size}")

        # 获取 UI 层次结构
        ui_dump = device.dump_ui_hierarchy()
        print(f"UI 层次结构长度: {len(ui_dump)} 字符")

    except Exception as e:
        print(f"设备信息获取失败: {e}")


def ui_analysis_example():
    """UI 分析示例"""
    print("=== UI 分析示例 ===")

    try:
        from android_automation import UIAnalyzer

        device = AndroidDevice()
        analyzer = UIAnalyzer(device)

        # 查找所有按钮
        buttons = analyzer.find_elements_by_class("android.widget.Button")
        print(f"找到 {len(buttons)} 个按钮:")

        for i, button in enumerate(buttons[:5]):  # 只显示前5个
            print(f"  {i+1}. {button.text} - {button.resource_id}")

        # 查找文本元素
        text_elements = analyzer.find_elements_by_class("android.widget.TextView")
        print(f"找到 {len(text_elements)} 个文本元素")

        # 查找特定文本
        specific_elements = analyzer.find_elements_by_text("微信")
        if specific_elements:
            element = specific_elements[0]
            print(f"找到'微信'元素: {element.bounds}")

    except Exception as e:
        print(f"UI 分析失败: {e}")


def advanced_automation_example():
    """高级自动化示例"""
    print("=== 高级自动化示例 ===")

    try:
        wechat = WeChatAutomation()

        # 启动微信
        wechat.start_wechat()

        # 截屏并分析当前界面
        screenshot_path = wechat.take_screenshot_with_annotation("current_ui.png")
        print(f"界面分析图片已保存: {screenshot_path}")

        # 查找特定联系人并发送多条消息
        contact_name = "测试联系人"
        messages = [
            "第一条消息",
            "第二条消息",
            "第三条消息"
        ]

        if wechat.find_contact(contact_name):
            for i, message in enumerate(messages, 1):
                success = wechat.send_message(f"{i}. {message}")
                if success:
                    print(f"✅ 第{i}条消息发送成功")
                else:
                    print(f"❌ 第{i}条消息发送失败")

                # 消息间隔
                import time
                time.sleep(2)

        # 获取聊天记录
        latest_messages = wechat.get_latest_messages(10)
        print(f"最新10条消息: {latest_messages}")

    except Exception as e:
        print(f"高级自动化示例失败: {e}")


if __name__ == "__main__":
    print("Android WeChat Automation Examples")
    print("=" * 50)

    # 运行示例
    try:
        # 基础示例
        basic_messaging_example()
        print()

        # 设备信息示例
        device_info_example()
        print()

        # UI 分析示例
        ui_analysis_example()
        print()

        # 高级自动化示例
        # advanced_automation_example()

    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"示例执行出错: {e}")

    print("\n示例执行完成!")