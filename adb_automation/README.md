# Android WeChat Automation - Built from Scratch

一个完全从零构建的 Android 微信自动化库，不依赖任何第三方自动化框架。

## 🚀 核心特性

- **纯 ADB 驱动**: 只使用 Android Debug Bridge，无需 root 权限
- **UI 自动化**: 通过 UI Automator 解析和操作界面元素
- **图像识别**: 支持模板匹配和 OCR 文字识别
- **微信专用**: 针对微信 Android 版本优化的操作接口
- **轻量级**: 最小依赖，易于部署和维护

## 📋 依赖要求

### 基础依赖
```bash
pip install pillow opencv-python numpy
```

### 可选依赖 (OCR 功能)
```bash
pip install pytesseract
# 需要安装 Tesseract OCR 引擎
```

### 系统要求
- Android 设备 (API 18+)
- 启用 USB 调试
- ADB 工具 (Android SDK Platform Tools)

## 🔧 快速开始

### 1. 设备准备

```bash
# 检查设备连接
adb devices

# 确保微信已安装
adb shell pm list packages | grep tencent
```

### 2. 基础使用

```python
from android_automation import WeChatAutomation

# 创建微信自动化实例
wechat = WeChatAutomation()

# 启动微信
wechat.start_wechat()

# 发送消息
wechat.send_message_to_contact("联系人名称", "Hello from automation!")

# 获取最新消息
messages = wechat.get_latest_messages(5)
print(messages)
```

### 3. UI 分析

```python
from android_automation import AndroidDevice, UIAnalyzer

device = AndroidDevice()
analyzer = UIAnalyzer(device)

# 查找元素
buttons = analyzer.find_elements_by_class("android.widget.Button")
text_elements = analyzer.find_elements_by_text("发送")

# 获取元素中心坐标并点击
if text_elements:
    center_x, center_y = analyzer.get_element_center(text_elements[0])
    device.tap(center_x, center_y)
```

### 4. 图像识别

```python
from android_automation import WeChatImageAutomation

image_auto = WeChatImageAutomation(device)

# 通过图像模板点击元素
image_auto.click_element_by_image("send_button")

# 等待元素出现
image_auto.wait_for_element_by_image("chat_window", timeout=10)

# 创建新模板
image_auto.create_template("new_button", (100, 200, 200, 300))
```

## 📚 架构设计

```
android_automation/
├── core.py                 # 核心 ADB 操作和 UI 分析
├── wechat_automation.py    # 微信专用自动化接口
├── image_recognition.py    # 图像识别和模板匹配
└── examples/              # 使用示例
    └── simple_usage.py    # 简单使用示例
```

### 核心组件

1. **AndroidDevice**: ADB 设备控制
   - 点击、滑动、输入操作
   - 应用启动和管理
   - 截屏和 UI dump

2. **UIAnalyzer**: UI 元素分析
   - XML 解析和元素查找
   - 坐标计算和元素过滤
   - 多种查找策略

3. **WeChatAutomation**: 微信自动化
   - 联系人查找和消息发送
   - 聊天记录获取
   - 微信专用操作流程

4. **ImageMatcher**: 图像识别
   - 模板匹配
   - OCR 文字识别
   - 元素定位和去重

## 🎯 使用场景

### 消息自动回复
```python
wechat = WeChatAutomation()
wechat.start_wechat()

# 监听和回复消息
messages = wechat.get_latest_messages(1)
if messages and "你好" in messages[0]:
    wechat.send_message("自动回复: 您好!")
```

### 批量消息发送
```python
contacts = ["张三", "李四", "王五"]
message = "群发消息内容"

for contact in contacts:
    success = wechat.send_message_to_contact(contact, message)
    print(f"向 {contact} 发送消息: {'成功' if success else '失败'}")
```

### UI 元素调试
```python
# 截屏并标注所有可点击元素
wechat.take_screenshot_with_annotation("debug_ui.png")

# 分析当前屏幕的 UI 结构
image_auto.analyze_current_screen("screen_analysis.png")
```

## ⚙️ 配置说明

### 微信资源 ID 配置

根据不同微信版本，可能需要调整 `wechat_automation.py` 中的资源 ID:

```python
# 微信 8.x 版本示例
SEARCH_BOX_ID = "com.tencent.mm:id/f8x"
CHAT_INPUT_ID = "com.tencent.mm:id/al_"
SEND_BUTTON_ID = "com.tencent.mm:id/anv"
```

### 图像识别配置

```python
# 调整匹配置信度
matcher = ImageMatcher(confidence_threshold=0.9)

# 设置模板目录
image_auto = WeChatImageAutomation(device, templates_dir="my_templates")
```

## 🚨 注意事项

1. **合规使用**: 请遵守微信使用条款，避免过度自动化
2. **版本兼容**: 微信更新可能导致 UI 元素变化
3. **稳定性**: 添加适当的等待时间和错误处理
4. **权限管理**: 确保应用有必要的权限 (通知、悬浮窗等)

## 🔍 故障排除

### 常见问题

1. **设备未连接**
   ```bash
   adb kill-server
   adb start-server
   adb devices
   ```

2. **权限不足**
   ```bash
   adb shell settings put secure enabled_accessibility_services com.android.talkback/com.android.talkback.TalkBackService
   ```

3. **元素查找失败**
   - 检查微信版本和资源 ID
   - 使用图像识别作为备用方案
   - 增加等待时间

4. **中文输入问题**
   ```python
   # 使用剪贴板输入中文
   device._run_adb_command(['shell', 'am', 'broadcast', '-a', 'clipper.set', '--es', 'text', '中文内容'])
   ```

## 📖 扩展开发

### 添加新功能

1. 继承 `WeChatAutomation` 类
2. 实现自定义操作方法
3. 添加错误处理和日志记录

```python
class CustomWeChatAutomation(WeChatAutomation):
    def send_image(self, image_path: str):
        # 实现图片发送功能
        pass

    def create_group_chat(self, members: List[str]):
        # 实现群聊创建功能
        pass
```

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 保存调试截图
wechat.take_screenshot_with_annotation(f"debug_{int(time.time())}.png")

# 输出 UI 结构
ui_dump = device.dump_ui_hierarchy()
with open("ui_dump.xml", "w", encoding="utf-8") as f:
    f.write(ui_dump)
```

## 📄 许可证

本项目仅供学习和研究使用，请勿用于违反相关服务条款的用途。