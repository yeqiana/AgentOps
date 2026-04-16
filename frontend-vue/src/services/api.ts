/**
 * API 服务层
 * 
 * 职责：
 * - 调用后端 POST /chat/stream 接口
 * - 处理流式 SSE 响应
 * - 解析事件并返回事件迭代器
 */

import type { StreamChatRequest, StreamEvent } from '../types/api';

/**
 * API 基础 URL - 开发环境通过 vite 代理访问
 * 在 vite.config.ts 中配置 /chat 代理到后端
 * 
 * 使用相对路径而不是绝对 URL，这样：
 * 1. Vite 代理可以正确拦截
 * 2. 避免浏览器直接跨域请求
 * 3. 生产环境可以无缝切换
 */
const API_BASE_URL = '';

/**
 * 解析 SSE 格式的完整事件
 * 
 * SSE 标准格式：
 * event: answer_delta
 * data: {"delta": "你"}
 * (空行)
 * 
 * 注意：JSON 中不包含 type 字段，type 来自 event: 行
 */
function parseSSEEvent(eventType: string | null, dataStr: string | null) {
  if (!eventType || !dataStr) {
    return null;
  }

  try {
    const data = JSON.parse(dataStr);
    
    // 将事件类型和数据合并
    return {
      type: eventType as any,
      ...data
    };
  } catch (error) {
    console.error('Failed to parse SSE data:', error, dataStr);
    return null;
  }
}

/**
 * 流式调用后端 API，返回异步迭代器
 * 
 * 处理完整的 SSE 事件流，每个事件由 event: 和 data: 行组成
 */
export async function* streamChat(
  request: StreamChatRequest
): AsyncGenerator<StreamEvent, void, unknown> {
  const url = `${API_BASE_URL}/chat/stream`;
  
  const payload = {
    message: request.message,
    session_id: request.session_id || null,
    user_name: request.user_name || 'api-user',
    session_title: request.session_title || 'API Session'
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      // 尝试解析错误响应
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.message || `API Error: ${response.status} ${response.statusText}`
      );
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Failed to get response stream reader');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let eventType: string | null = null;
    let eventData: string | null = null;

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        buffer += decoder.decode(value, { stream: !done });
        
        if (done && buffer.length === 0) {
          break;
        }

        // 按行处理
        const lines = buffer.split('\n');
        
        // 保留最后一个可能不完整的行在 buffer 中
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          
          // 空行表示事件结束
          if (!trimmed) {
            if (eventType && eventData) {
              const event = parseSSEEvent(eventType, eventData);
              if (event) {
                yield event;
                
                // 如果是 done 事件，停止迭代
                if (event.type === 'done') {
                  return;
                }
              }
            }
            // 重置当前事件
            eventType = null;
            eventData = null;
            continue;
          }
          
          // 跳过注释行
          if (trimmed.startsWith(':')) {
            continue;
          }
          
          // 解析 event: 行
          if (trimmed.startsWith('event:')) {
            eventType = trimmed.slice(6).trim();
            continue;
          }
          
          // 解析 data: 行
          if (trimmed.startsWith('data:')) {
            eventData = trimmed.slice(5).trim();
            continue;
          }
        }
      }

      // 处理 buffer 中剩余的不完整事件
      if (buffer.trim()) {
        const trimmed = buffer.trim();
        if (trimmed.startsWith('event:')) {
          eventType = trimmed.slice(6).trim();
        } else if (trimmed.startsWith('data:')) {
          eventData = trimmed.slice(5).trim();
        }
        
        if (eventType && eventData) {
          const event = parseSSEEvent(eventType, eventData);
          if (event) {
            yield event;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    // 抛出错误让调用方处理
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('Stream chat error:', message);
    throw error;
  }
}

/**
 * 生成唯一的消息 ID
 */
export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
