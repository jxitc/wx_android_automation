"""
Android WeChat Automation Package
Android 微信自动化包 - 从零构建

这是一个完全从零构建的 Android 自动化库，专门用于微信自动化操作。
不依赖任何第三方自动化框架，只使用 ADB 和图像识别技术。
"""

from .core import AndroidDevice, UIAnalyzer, UIElement
from .wechat_automation import WeChatAutomation
from .image_recognition import ImageMatcher, WeChatImageAutomation

__version__ = "1.0.0"
__author__ = "Built from scratch"

__all__ = [
    'AndroidDevice',
    'UIAnalyzer',
    'UIElement',
    'WeChatAutomation',
    'ImageMatcher',
    'WeChatImageAutomation'
]