/**
 * API 类型定义
 */

export interface StreamChatRequest {
  message: string;
  session_id?: string;
  user_name?: string;
  session_title?: string;
}

export type StreamEventType = 'metadata' | 'answer_delta' | 'done' | 'error';

export interface StreamMetadataEvent {
  type: 'metadata';
  session_id: string;
  turn_id: string;
  task_id: string;
  trace_id: string;
  route_name: string;
  route_reason: string;
  execution_mode: string;
  protocol_summary: string;
}

export interface StreamAnswerDeltaEvent {
  type: 'answer_delta';
  delta: string;
}

export interface StreamDoneEvent {
  type: 'done';
  session_id: string;
  turn_id: string;
  task_id: string;
  trace_id: string;
  answer: string;
  review_status?: string;
  review_summary?: string;
  plan?: string;
  debate_summary?: string;
  arbitration_summary?: string;
  critic_summary?: string;
}

export interface StreamErrorEvent {
  type: 'error';
  code?: string;
  message: string;
}

export type StreamEvent = StreamMetadataEvent | StreamAnswerDeltaEvent | StreamDoneEvent | StreamErrorEvent;

export interface UploadAssetRequest {
  file: File;
  kind?: string;
  prompt?: string;
  session_id?: string;
  user_name?: string;
  session_title?: string;
}

export interface UploadAssetResponse {
  session_id: string;
  turn_id: string;
  task_id: string;
  trace_id: string;
  upload_dir: string;
  saved_path: string;
  inferred_kind: string;
  user_input: string;
  route_name: string;
  route_reason: string;
  input_assets: Array<Record<string, unknown>>;
  tool_results: Array<Record<string, unknown>>;
  task_state: string;
  available_tools: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}
