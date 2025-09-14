# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a WeChat Android automation project with two distinct implementation approaches:

1. **ADB-based automation** (`adb_automation/`) - Python library using ADB commands for device control
2. **Standalone Android app** (`android_standalone/`) - Native Android accessibility service

## Development Commands

### ADB Automation (Python)
```bash
# Install Python dependencies (as listed in README)
pip install pillow opencv-python numpy
pip install pytesseract  # Optional for OCR

# Test device connection
adb devices

# Check WeChat installation
adb shell pm list packages | grep tencent

# Basic usage test
cd adb_automation
python examples/simple_usage.py
```

### Android Standalone App (Java)
```bash
# Build the accessibility service app
./gradlew assembleDebug

# Install on device
adb install app-debug.apk

# Enable accessibility service manually through device settings
```

## Architecture

### ADB Automation Package Structure
- `core.py` - Core ADB operations and UI analysis using AndroidDevice and UIAnalyzer classes
- `wechat_automation.py` - WeChat-specific automation using WeChatAutomation class
- `image_recognition.py` - Template matching and OCR using ImageMatcher and WeChatImageAutomation
- `smart_element_finder.py` - Advanced element location strategies
- `examples/simple_usage.py` - Usage examples and patterns

### Key Classes and Their Responsibilities
- **AndroidDevice**: Low-level ADB device control (tapping, swiping, app management, screenshots)
- **UIAnalyzer**: UI hierarchy parsing and element discovery from XML dumps
- **WeChatAutomation**: High-level WeChat operations (message sending, contact finding)
- **ImageMatcher**: Computer vision for element detection when UI analysis fails
- **WeChatImageAutomation**: Combines image recognition with WeChat workflows

### Android Accessibility Service
- `WeChatAutomationService.java` - Main accessibility service for standalone operation
- `AndroidManifest.xml` - App configuration and permissions
- `accessibility_service_config.xml` - Service configuration

## Important Implementation Details

### WeChat Resource IDs
WeChat UI elements use specific resource IDs that may change between versions:
```python
SEARCH_BOX_ID = "com.tencent.mm:id/f8x"
CHAT_INPUT_ID = "com.tencent.mm:id/al_"
SEND_BUTTON_ID = "com.tencent.mm:id/anv"
```

### Multi-Strategy Element Finding
The codebase implements fallback strategies:
1. First try UI hierarchy analysis (fast, reliable)
2. Fall back to image recognition (slower, more robust)
3. Use smart element finder for complex scenarios

### Device Requirements
- Android API 18+ with USB debugging enabled
- ADB tools from Android SDK Platform Tools
- WeChat app installed and configured

## Testing and Debugging

### Debug UI Elements
```python
# Take annotated screenshots for debugging
wechat.take_screenshot_with_annotation("debug_ui.png")

# Dump UI hierarchy for analysis
ui_dump = device.dump_ui_hierarchy()
with open("ui_dump.xml", "w", encoding="utf-8") as f:
    f.write(ui_dump)
```

### Common Issues
- **Device connection**: Use `adb kill-server && adb start-server` to reset
- **Element not found**: WeChat version may have changed resource IDs
- **Chinese input**: Use clipboard method for non-ASCII text input
- **Permissions**: Accessibility service requires manual enablement in Settings

## Code Patterns

### Error Handling
Most operations include timeout parameters and retry logic. Always check return values from automation methods.

### Threading and Timing
The automation includes strategic delays (`time.sleep()`) between operations to allow UI transitions. Adjust timing based on device performance.

### Fallback Strategies
When UI-based automation fails, image recognition provides a backup method. Templates are stored in configurable directories.