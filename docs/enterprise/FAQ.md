# FAQ

## 1. 不配置豆包、OpenAI 等真实模型，系统还能不能对话？

可以。

只要配置为 `mock` 模式，系统仍然可以正常跑通：
- CLI 对话
- API 对话
- SSE 流式对话
- 工作流主链
- 多 Agent 最小编排
- trace、task、alert、tool_results 持久化与查询

说明：
- `mock` 适合开发、联调、测试和验证链路
- `mock` 不代表真实模型质量

## 2. 为什么上传文件后没有触发 OCR 或 ASR？

常见原因如下：
- `run_tools=false`
- 对应工具路径未配置
- 本机未安装 `tesseract`
- 本机未安装 `ffmpeg`
- 本机未安装 `whisper`
- 上传类型不在允许范围内
- 上传文件超过大小限制

## 3. 为什么默认上传目录是 `/app/download`？

原因如下：
- 这是统一默认值，便于容器化和部署环境保持一致
- 当前支持通过 `APP_DOWNLOAD_DIR` 覆盖

## 4. 为什么当前数据库还是 SQLite？

原因如下：
- 当前阶段重点是先形成闭环与治理能力
- SQLite 足以支撑当前单机开发、测试和阶段 2 中期能力验证
- 后续可以演进到 PostgreSQL

## 5. 如何查看失败任务？

可通过以下接口查询：
- `GET /tasks?status=failed`
- `GET /tasks/{task_id}`
- `GET /alerts`
- `GET /traces/{trace_id}/alerts`

## 6. 当前是否已经支持统一鉴权？

已经支持最小统一鉴权。

当前支持：
- `X-API-Key`
- `Authorization: Bearer ...`

当前未完成：
- 完整 RBAC
- 资源级授权
- 工具级授权

## 7. 当前是否已经支持多 Agent 编排？

已经支持最小多 Agent 编排。

当前已落地：
- `router`
- `debate`
- `arbitration`
- `critic`
- `review`

当前未完成：
- 更复杂的多 Agent 协作协议
- 更强的角色治理

## 8. 当前是否已经支持流式对话？

已经支持。

当前支持：
- CLI 流式输出
- `POST /chat/stream` 的 SSE 流式返回

## 9. 当前是否已经支持可视化 trace？

还没有。

当前已支持：
- trace 落库
- trace 查询
- trace 与 task 关联
- trace 与 alert 关联

当前未完成：
- trace 可视化页面
- 观测面板

## 10. 当前是否已经支持异步任务体系？

还没有完整支持。

当前已具备：
- `task_id`
- 任务落库
- 任务状态查询

当前未具备：
- 队列
- worker
- 异步提交
- 后台消费执行
