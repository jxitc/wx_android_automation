# WeChat Android Automation

Cross-platform WeChat automation with two implementation approaches:

## 🔧 Quick Start

### Option 1: ADB-based Python Automation
```bash
# Install dependencies
pip install pillow opencv-python numpy

# Connect Android device with USB debugging enabled
adb devices

# Run automation
cd adb_automation
python examples/simple_usage.py
```

### Option 2: Standalone Android App
```bash
# Build and install accessibility service
./gradlew assembleDebug
adb install app-debug.apk

# Enable in Settings → Accessibility → WeChat Automation
```

## 📁 Project Structure

- `adb_automation/` - Python library using ADB commands
- `android_standalone/` - Native Android accessibility service
- `CLAUDE.md` - Development guidance for Claude Code

## 🚀 Features

- Message sending and receiving
- Contact management
- Image recognition fallback
- UI element automation
- Standalone phone operation (no computer required)

## 📋 Requirements

- Android device (API 18+)
- USB debugging enabled
- WeChat app installed
- ADB tools (for Python approach)

See individual directories for detailed documentation and usage examples.