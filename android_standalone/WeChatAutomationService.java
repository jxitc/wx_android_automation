/**
 * WeChat Automation Accessibility Service
 * 微信自动化无障碍服务 - 独立运行在 Android 设备上
 */

package com.example.wechatautomation;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Rect;
import android.os.Bundle;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.List;

public class WeChatAutomationService extends AccessibilityService {

    private static final String TAG = "WeChatAutomation";
    private static final String WECHAT_PACKAGE = "com.tencent.mm";

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        String packageName = event.getPackageName().toString();

        // 只处理微信应用的事件
        if (!WECHAT_PACKAGE.equals(packageName)) {
            return;
        }

        int eventType = event.getEventType();
        Log.d(TAG, "WeChat event: " + AccessibilityEvent.eventTypeToString(eventType));

        switch (eventType) {
            case AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED:
                handleNewMessage(event);
                break;
            case AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED:
                handleWindowChange(event);
                break;
            case AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED:
                handleContentChange(event);
                break;
        }
    }

    /**
     * 处理新消息通知
     */
    private void handleNewMessage(AccessibilityEvent event) {
        CharSequence text = event.getText().toString();
        Log.d(TAG, "New message: " + text);

        // 可以在这里实现自动回复逻辑
        if (shouldAutoReply(text.toString())) {
            openWeChatAndReply(text.toString());
        }
    }

    /**
     * 判断是否需要自动回复
     */
    private boolean shouldAutoReply(String message) {
        // 实现自定义回复规则
        return message.contains("你好") ||
               message.contains("在吗") ||
               message.contains("hello");
    }

    /**
     * 打开微信并回复消息
     */
    private void openWeChatAndReply(String originalMessage) {
        try {
            // 等待界面加载
            Thread.sleep(2000);

            AccessibilityNodeInfo rootNode = getRootInActiveWindow();
            if (rootNode == null) return;

            // 查找并点击最新的聊天
            clickLatestChat(rootNode);

            // 等待聊天界面打开
            Thread.sleep(1500);

            // 发送自动回复
            String reply = generateAutoReply(originalMessage);
            sendMessage(reply);

        } catch (InterruptedException e) {
            Log.e(TAG, "Sleep interrupted", e);
        }
    }

    /**
     * 点击最新的聊天
     */
    private void clickLatestChat(AccessibilityNodeInfo rootNode) {
        // 查找聊天列表中的第一个聊天项
        List<AccessibilityNodeInfo> chatItems =
            rootNode.findAccessibilityNodeInfosByViewId("com.tencent.mm:id/e3k");

        if (!chatItems.isEmpty()) {
            AccessibilityNodeInfo firstChat = chatItems.get(0);
            clickNode(firstChat);
            Log.d(TAG, "Clicked latest chat");
        }
    }

    /**
     * 发送消息
     */
    private void sendMessage(String message) {
        AccessibilityNodeInfo rootNode = getRootInActiveWindow();
        if (rootNode == null) return;

        // 查找输入框
        List<AccessibilityNodeInfo> inputBoxes =
            rootNode.findAccessibilityNodeInfosByViewId("com.tencent.mm:id/al_");

        if (!inputBoxes.isEmpty()) {
            AccessibilityNodeInfo inputBox = inputBoxes.get(0);

            // 输入文本
            Bundle arguments = new Bundle();
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, message);
            inputBox.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments);

            Log.d(TAG, "Text entered: " + message);

            // 查找并点击发送按钮
            List<AccessibilityNodeInfo> sendButtons =
                rootNode.findAccessibilityNodeInfosByViewId("com.tencent.mm:id/anv");

            if (!sendButtons.isEmpty()) {
                clickNode(sendButtons.get(0));
                Log.d(TAG, "Message sent: " + message);
            }
        }
    }

    /**
     * 生成自动回复内容
     */
    private String generateAutoReply(String originalMessage) {
        if (originalMessage.contains("你好") || originalMessage.contains("hello")) {
            return "您好！我现在不在，稍后回复您。";
        } else if (originalMessage.contains("在吗")) {
            return "我现在有事，一会儿联系您。";
        } else {
            return "收到您的消息，稍后回复。";
        }
    }

    /**
     * 点击节点
     */
    private void clickNode(AccessibilityNodeInfo node) {
        if (node == null) return;

        Rect bounds = new Rect();
        node.getBoundsInScreen(bounds);

        // 计算点击坐标
        int x = bounds.centerX();
        int y = bounds.centerY();

        // 创建手势路径
        Path clickPath = new Path();
        clickPath.moveTo(x, y);

        // 创建手势描述
        GestureDescription.StrokeDescription clickStroke =
            new GestureDescription.StrokeDescription(clickPath, 0, 100);

        GestureDescription clickGesture = new GestureDescription.Builder()
            .addStroke(clickStroke)
            .build();

        // 执行手势
        dispatchGesture(clickGesture, null, null);

        Log.d(TAG, "Clicked at: " + x + ", " + y);
    }

    /**
     * 查找包含指定文本的节点
     */
    private AccessibilityNodeInfo findNodeByText(AccessibilityNodeInfo rootNode, String text) {
        if (rootNode == null) return null;

        List<AccessibilityNodeInfo> nodes = rootNode.findAccessibilityNodeInfosByText(text);
        return nodes.isEmpty() ? null : nodes.get(0);
    }

    /**
     * 递归查找可点击的节点
     */
    private AccessibilityNodeInfo findClickableNode(AccessibilityNodeInfo node) {
        if (node == null) return null;

        if (node.isClickable()) {
            return node;
        }

        // 递归查找子节点
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo clickable = findClickableNode(child);
            if (clickable != null) {
                return clickable;
            }
        }

        return null;
    }

    private void handleWindowChange(AccessibilityEvent event) {
        String className = event.getClassName().toString();
        Log.d(TAG, "Window changed: " + className);

        // 可以根据窗口变化执行特定操作
        if (className.contains("LauncherUI")) {
            Log.d(TAG, "WeChat main window opened");
        } else if (className.contains("ChattingUI")) {
            Log.d(TAG, "Chat window opened");
        }
    }

    private void handleContentChange(AccessibilityEvent event) {
        // 处理内容变化，如新消息到达
        AccessibilityNodeInfo source = event.getSource();
        if (source != null) {
            CharSequence text = source.getText();
            if (text != null && text.length() > 0) {
                Log.d(TAG, "Content changed: " + text);
            }
        }
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "Service interrupted");
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        Log.d(TAG, "WeChat Automation Service connected");
    }

    @Override
    public boolean onUnbind(Intent intent) {
        Log.d(TAG, "Service unbound");
        return super.onUnbind(intent);
    }
}