"""
Smart Element Finder with Caching
智能元素查找器 - 带缓存优化
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from PIL import Image
import os

from .core import AndroidDevice, UIAnalyzer, UIElement
from .image_recognition import ImageMatcher


@dataclass
class CachedElement:
    """缓存的元素信息"""
    resource_id: str
    bounds: Tuple[int, int, int, int]
    text: str
    class_name: str
    timestamp: float
    confidence: float
    method: str  # 'resource_id', 'text', 'image', 'ocr'


class SmartElementFinder:
    """智能元素查找器 - 优先使用快速方法，必要时才使用图像识别"""

    def __init__(self, device: AndroidDevice, cache_dir: str = "element_cache"):
        self.device = device
        self.analyzer = UIAnalyzer(device)
        self.image_matcher = ImageMatcher()
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "element_cache.json")
        self.element_cache: Dict[str, CachedElement] = {}

        # 缓存配置
        self.cache_ttl = 300  # 缓存5分钟
        self.image_cache_ttl = 60  # 图像缓存1分钟（更短，因为UI变化频繁）

        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cache()

    def _load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                for key, data in cache_data.items():
                    self.element_cache[key] = CachedElement(**data)

                print(f"📚 加载了 {len(self.element_cache)} 个缓存元素")
            except Exception as e:
                print(f"⚠️ 缓存加载失败: {e}")

    def _save_cache(self):
        """保存缓存"""
        try:
            cache_data = {}
            for key, element in self.element_cache.items():
                cache_data[key] = asdict(element)

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")

    def _is_cache_valid(self, element: CachedElement) -> bool:
        """检查缓存是否仍然有效"""
        current_time = time.time()

        # 根据查找方法设置不同的过期时间
        if element.method in ['image', 'ocr']:
            ttl = self.image_cache_ttl
        else:
            ttl = self.cache_ttl

        return (current_time - element.timestamp) < ttl

    def _generate_cache_key(self, identifier: str, method: str) -> str:
        """生成缓存键"""
        return f"{method}:{identifier}"

    def find_element(self, identifier: str,
                    method: str = "auto",
                    template_path: str = None) -> Optional[UIElement]:
        """
        智能查找元素 - 优先使用快速方法

        Args:
            identifier: 元素标识符 (resource_id, text, 或图像模板名)
            method: 查找方法 ('auto', 'resource_id', 'text', 'image', 'ocr')
            template_path: 图像模板路径 (仅当method='image'时需要)
        """
        print(f"🔍 查找元素: {identifier} (方法: {method})")

        # 1. 检查缓存
        cache_key = self._generate_cache_key(identifier, method)
        if cache_key in self.element_cache:
            cached = self.element_cache[cache_key]
            if self._is_cache_valid(cached):
                # 验证缓存元素是否仍然存在
                if self._verify_cached_element(cached):
                    print(f"✅ 使用缓存元素: {identifier}")
                    return UIElement(
                        resource_id=cached.resource_id,
                        text=cached.text,
                        class_name=cached.class_name,
                        bounds=cached.bounds,
                        clickable=True,
                        enabled=True
                    )
                else:
                    print(f"🗑️ 缓存元素已失效，删除缓存: {identifier}")
                    del self.element_cache[cache_key]

        # 2. 根据方法查找元素
        element = None
        method_used = method

        if method == "auto":
            # 自动选择最佳方法
            element, method_used = self._auto_find_element(identifier, template_path)
        elif method == "resource_id":
            element = self._find_by_resource_id(identifier)
        elif method == "text":
            element = self._find_by_text(identifier)
        elif method == "image":
            element = self._find_by_image(template_path or identifier)
        elif method == "ocr":
            element = self._find_by_ocr(identifier)
        else:
            raise ValueError(f"不支持的查找方法: {method}")

        # 3. 缓存结果
        if element:
            self._cache_element(identifier, element, method_used)

        return element

    def _auto_find_element(self, identifier: str,
                          template_path: str = None) -> Tuple[Optional[UIElement], str]:
        """自动选择最佳查找方法"""

        # 策略1: 如果identifier看起来像resource_id，先尝试resource_id
        if ":" in identifier and "/" in identifier:
            print("🎯 尝试 resource_id 方法...")
            element = self._find_by_resource_id(identifier)
            if element:
                return element, "resource_id"

        # 策略2: 尝试文本查找 (快速)
        print("🎯 尝试文本查找...")
        element = self._find_by_text(identifier)
        if element:
            return element, "text"

        # 策略3: 如果有模板路径，尝试图像匹配
        if template_path and os.path.exists(template_path):
            print("🎯 尝试图像匹配...")
            element = self._find_by_image(template_path)
            if element:
                return element, "image"

        # 策略4: 最后尝试OCR (最慢)
        print("🎯 尝试 OCR 文字识别...")
        element = self._find_by_ocr(identifier)
        if element:
            return element, "ocr"

        return None, "none"

    def _find_by_resource_id(self, resource_id: str) -> Optional[UIElement]:
        """通过resource_id查找"""
        elements = self.analyzer.find_elements_by_resource_id(resource_id)
        return elements[0] if elements else None

    def _find_by_text(self, text: str) -> Optional[UIElement]:
        """通过文本查找"""
        elements = self.analyzer.find_elements_by_text(text)
        return elements[0] if elements else None

    def _find_by_image(self, template_path: str) -> Optional[UIElement]:
        """通过图像模板查找"""
        if not os.path.exists(template_path):
            return None

        screenshot = self.device.take_screenshot()
        bounds = self.image_matcher.find_element_by_template(screenshot, template_path)

        if bounds:
            return UIElement(
                resource_id="",
                text="",
                class_name="ImageMatched",
                bounds=bounds,
                clickable=True,
                enabled=True
            )
        return None

    def _find_by_ocr(self, text: str) -> Optional[UIElement]:
        """通过OCR查找"""
        try:
            screenshot = self.device.take_screenshot()
            bounds_list = self.image_matcher.find_text_by_ocr(screenshot, text)

            if bounds_list:
                return UIElement(
                    resource_id="",
                    text=text,
                    class_name="OCRMatched",
                    bounds=bounds_list[0],
                    clickable=True,
                    enabled=True
                )
        except Exception as e:
            print(f"OCR 查找失败: {e}")

        return None

    def _verify_cached_element(self, cached: CachedElement) -> bool:
        """验证缓存的元素是否仍然存在"""
        try:
            # 快速验证：检查该位置是否还有可点击元素
            left, top, right, bottom = cached.bounds
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2

            # 获取当前UI状态
            xml_content = self.device.dump_ui_hierarchy()
            all_elements = self.analyzer._parse_elements_from_xml(xml_content)

            # 检查是否有元素在相同位置
            for element in all_elements:
                if element.bounds and self._bounds_overlap(element.bounds, cached.bounds):
                    return True

            return False

        except Exception:
            return False

    def _bounds_overlap(self, bounds1: Tuple[int, int, int, int],
                       bounds2: Tuple[int, int, int, int], threshold: float = 0.8) -> bool:
        """检查两个边界是否重叠"""
        x1_left, y1_top, x1_right, y1_bottom = bounds1
        x2_left, y2_top, x2_right, y2_bottom = bounds2

        # 计算重叠面积
        overlap_left = max(x1_left, x2_left)
        overlap_top = max(y1_top, y2_top)
        overlap_right = min(x1_right, x2_right)
        overlap_bottom = min(y1_bottom, y2_bottom)

        if overlap_right <= overlap_left or overlap_bottom <= overlap_top:
            return False

        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
        bounds1_area = (x1_right - x1_left) * (y1_bottom - y1_top)

        return (overlap_area / bounds1_area) >= threshold

    def _cache_element(self, identifier: str, element: UIElement, method: str):
        """缓存元素"""
        cache_key = self._generate_cache_key(identifier, method)

        cached_element = CachedElement(
            resource_id=element.resource_id,
            bounds=element.bounds,
            text=element.text,
            class_name=element.class_name,
            timestamp=time.time(),
            confidence=1.0,  # 可以根据查找方法调整
            method=method
        )

        self.element_cache[cache_key] = cached_element
        self._save_cache()
        print(f"💾 缓存元素: {identifier} (方法: {method})")

    def click_element(self, identifier: str, **kwargs) -> bool:
        """点击元素 - 智能查找并点击"""
        element = self.find_element(identifier, **kwargs)

        if element:
            center_x, center_y = self.analyzer.get_element_center(element)
            self.device.tap(center_x, center_y)
            print(f"✅ 点击元素成功: {identifier}")
            return True
        else:
            print(f"❌ 未找到元素: {identifier}")
            return False

    def clear_cache(self):
        """清除所有缓存"""
        self.element_cache.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ 缓存已清除")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        current_time = time.time()
        valid_count = 0
        method_stats = {}

        for element in self.element_cache.values():
            if self._is_cache_valid(element):
                valid_count += 1

            method = element.method
            method_stats[method] = method_stats.get(method, 0) + 1

        return {
            "total_cached": len(self.element_cache),
            "valid_cached": valid_count,
            "method_distribution": method_stats,
            "cache_hit_potential": f"{(valid_count/len(self.element_cache)*100):.1f}%" if self.element_cache else "0%"
        }


# 使用示例
if __name__ == "__main__":
    print("=== 智能元素查找器测试 ===")

    try:
        from .core import AndroidDevice

        device = AndroidDevice()
        finder = SmartElementFinder(device)

        # 测试不同的查找方法
        test_cases = [
            ("com.tencent.mm:id/send_btn", "auto"),
            ("发送", "auto"),
            ("微信", "text"),
        ]

        for identifier, method in test_cases:
            print(f"\n测试查找: {identifier}")

            # 第一次查找 (会进行实际搜索)
            start_time = time.time()
            element1 = finder.find_element(identifier, method=method)
            first_time = time.time() - start_time

            # 第二次查找 (应该使用缓存)
            start_time = time.time()
            element2 = finder.find_element(identifier, method=method)
            second_time = time.time() - start_time

            print(f"第一次查找: {first_time:.3f}s, 第二次查找: {second_time:.3f}s")
            print(f"缓存效果: {((first_time - second_time) / first_time * 100):.1f}% 速度提升")

        # 显示缓存统计
        stats = finder.get_cache_stats()
        print(f"\n缓存统计: {stats}")

    except Exception as e:
        print(f"测试失败: {e}")