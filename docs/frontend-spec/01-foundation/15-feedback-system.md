# 反馈系统规范

## 一、反馈类型
- Toast / Message
- Notification
- Inline Alert
- Modal
- Popconfirm
- Result 页面

## 二、使用场景
- 轻成功：Toast
- 高风险操作确认：Popconfirm / Modal
- 页面级失败：Inline Alert / Result
- 持续关注类消息：Notification

## 三、原则
- 成功提示轻量
- 危险操作必须有确认
- 错误信息要可读，不可只给错误码
