# FAQ

## 1. 为什么上传文件后没有触发 OCR？

可能原因：
- `run_tools=false`
- `OCR_TOOL_PATH` 未配置
- 本机未安装 `tesseract`

## 2. 为什么视频没有做 ASR？

可能原因：
- `VIDEO_AUDIO_TOOL_PATH` 未配置
- `ASR_TOOL_PATH` 未配置
- 本机未安装 `ffmpeg` 或 `whisper`

## 3. 为什么默认上传目录是 `/app/download`？

原因：
- 这是统一默认值，便于容器化和企业部署口径一致
- 同时支持通过 `APP_DOWNLOAD_DIR` 覆盖

## 4. 为什么当前数据库还是 SQLite？

原因：
- 阶段 1 目标是先形成闭环
- 后续可切 PostgreSQL

## 5. 如何查失败任务？

查询：
- `GET /tasks?status=failed`
- `GET /tasks/{task_id}`
