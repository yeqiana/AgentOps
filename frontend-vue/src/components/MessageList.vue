<template>
  <section class="message-list">
    <div
      v-for="message in messages"
      :key="message.id"
      class="message"
      :class="[`message--${message.role}`]"
    >
      <div class="message__role">
        {{ message.role === 'user' ? t('chat.user') : t('chat.assistant') }}
      </div>
      <div v-if="message.role === 'user'" class="message__content message__content--text">
        {{ message.content }}
      </div>
      <div
        v-else
        class="message__content message__content--markdown"
        v-html="renderMarkdown(message.content)"
      ></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { marked } from 'marked';
import type { ChatMessage } from '../types/api';

defineProps<{
  messages: ChatMessage[];
}>();

const { t } = useI18n();

// 全局配置 marked，避免每次渲染都重复设置
marked.setOptions({
  gfm: true,
  breaks: false,
  headerIds: false,
  mangle: false,
  smartLists: true,
  smartypants: false
});

/**
 * 使用 marked 库进行完整的 Markdown 渲染
 * 支持：
 * - 标题、粗体、斜体、代码
 * - 代码块（带语言高亮提示）
 * - 列表、引用、链接等
 * - 表格等高级语法
 */
function renderMarkdown(markdown: string): string {
  try {
    if (!markdown) {
      return '';
    }

    // 基于完整文本重新渲染，保留所有换行和 Markdown 结构
    return marked.parse(markdown);
  } catch (error) {
    console.error('Markdown rendering error:', error);
    // 如果渲染失败，返回纯文本（已转义）
    return escapeHtml(markdown);
  }
}

/**
 * 转义 HTML 特殊字符，防止 XSS 注入
 */
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, (char) => map[char]);
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 8px;
  animation: slideIn 0.3s ease-in-out;
}

.message--user {
  align-items: flex-end;
}

.message--assistant {
  align-items: flex-start;
}

.message__role {
  font-size: 12px;
  color: #999;
  text-transform: capitalize;
}

.message__content {
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  max-width: 70%;
  word-wrap: break-word;
}

.message--user .message__content {
  background-color: #0084ff;
  color: white;
  border-radius: 12px 12px 4px 12px;
}

.message--user .message__content--text {
  font-size: 14px;
}

.message--assistant .message__content {
  background-color: #f1f1f1;
  color: #333;
  border-radius: 12px 12px 12px 4px;
}

.message__content--markdown {
  font-size: 14px;
}

/* Markdown 样式 - 使用 :deep() 穿透作用域限制 */
.message__content--markdown :deep(h1),
.message__content--markdown :deep(h2),
.message__content--markdown :deep(h3),
.message__content--markdown :deep(h4),
.message__content--markdown :deep(h5),
.message__content--markdown :deep(h6) {
  margin: 12px 0 8px 0;
  font-weight: 600;
}

.message__content--markdown :deep(h1) {
  font-size: 20px;
}

.message__content--markdown :deep(h2) {
  font-size: 18px;
}

.message__content--markdown :deep(h3) {
  font-size: 16px;
}

.message__content--markdown :deep(h4),
.message__content--markdown :deep(h5),
.message__content--markdown :deep(h6) {
  font-size: 14px;
}

.message__content--markdown :deep(strong) {
  font-weight: 600;
}

.message__content--markdown :deep(em) {
  font-style: italic;
}

.message__content--markdown :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.message__content--markdown :deep(pre) {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.message__content--markdown :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-size: 13px;
}

.message__content--markdown :deep(ul),
.message__content--markdown :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message__content--markdown :deep(li) {
  margin: 4px 0;
}

.message__content--markdown :deep(blockquote) {
  border-left: 3px solid #d0d0d0;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
}

.message__content--markdown :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 13px;
}

.message__content--markdown :deep(table thead) {
  background-color: #f5f5f5;
}

.message__content--markdown :deep(table th),
.message__content--markdown :deep(table td) {
  border: 1px solid #e0e0e0;
  padding: 8px 12px;
  text-align: left;
}

.message__content--markdown :deep(table tr:nth-child(even)) {
  background-color: #fafafa;
}

.message__content--markdown :deep(a) {
  color: #0084ff;
  text-decoration: none;
}

.message__content--markdown :deep(a:hover) {
  text-decoration: underline;
}

.message__content--markdown :deep(p) {
  margin: 6px 0;
}

.message__content--markdown :deep(hr) {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 8px 0;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式：小屏幕上消息占用更多宽度 */
@media (max-width: 768px) {
  .message__content {
    max-width: 90%;
  }
}
</style>
