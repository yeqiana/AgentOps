
<template>
  <div class="chat-redesign-page">
    <!-- 左侧会话栏：用户在这里切换 tab、搜索会话、选择会话。 -->
    <aside class="chat-sidebar" :aria-label="t('sidebar.aria')">
      <div class="chat-sidebar__top">
        <!-- 用户点击品牌区 -> 预留打开工作区菜单，目前只保留按钮状态。 -->
        <button class="chat-sidebar__brand" type="button" :aria-label="t('sidebar.brandMenu')">
          <ChatLogo compact />
          <ArrowDown class="chat-sidebar__chevron" />
        </button>
        <!-- 用户点击关闭按钮 -> 预留关闭侧边栏，目前只保留视觉和交互态。 -->
        <IconButton :icon="Close" :label="t('sidebar.close')" size="lg" />
      </div>

      <div class="chat-sidebar__body">
        <!-- 用户点击“聊天 / 收藏” -> activeTab 改变 -> tab 选中样式变化。 -->
        <SidebarTabs v-model="activeTab" />

        <!-- 用户输入搜索词 -> search 改变 -> filteredToday / filteredYesterday 重新过滤列表。 -->
        <label class="chat-sidebar__search">
          <Search />
          <input
            v-model="search"
            :aria-label="t('sidebar.search')"
            :placeholder="t('sidebar.searchPlaceholder')"
            type="search"
          />
        </label>

        <!-- 用户点击今天的会话 -> activeConversation 改变 -> 对应会话显示选中态。 -->
        <ConversationList v-model="activeConversation" :title="t('sidebar.groups.today')" :items="filteredToday" />
        <!-- 用户点击昨天的会话 -> activeConversation 改变 -> 对应会话显示选中态。 -->
        <ConversationList v-model="activeConversation" :title="t('sidebar.groups.yesterday')" :items="filteredYesterday" />
      </div>

      <!-- 用户点击底部图标 -> 预留主题、通知、个人资料入口，目前只保留基础按钮态。 -->
      <nav class="chat-sidebar__rail" :aria-label="t('sidebar.actions.profile')">
        <IconButton :icon="Sunny" :label="t('sidebar.actions.toggleTheme')" size="sm" />
        <IconButton :icon="Bell" :label="t('sidebar.actions.notifications')" size="sm" />
        <IconButton :icon="User" :label="t('sidebar.actions.profile')" size="sm" />
      </nav>
    </aside>

    <!-- 主内容区：展示欢迎卡片或消息列表，以及底部输入栏。 -->
    <section class="chat-main">
      <!-- 如果没有消息，显示欢迎区；有消息时显示消息列表 -->
      <template v-if="messages.length === 0">
        <WelcomePanel @select-prompt="usePrompt" />
      </template>
      <template v-else>
        <MessageList :messages="messages" />
      </template>

      <!-- 错误提示 -->
      <div v-if="errorMessage" class="chat-error">
        <span class="chat-error__icon">⚠️</span>
        <span class="chat-error__text">{{ errorMessage }}</span>
        <button class="chat-error__close" type="button" @click="errorMessage = ''">×</button>
      </div>

      <!-- 用户输入消息 -> draft 更新；点击新建聊天 -> resetDraft；点击发送 -> sendMessage。 -->
      <ChatComposer
      v-model="draft"
      :is-loading="isStreaming"
      @new-chat="resetDraft"
      @send="sendMessage"
    />
    </section>
  </div>
</template>
<!--
页面说明（人话版）

1. 页面是干嘛的

这是一个 ChatGPT 风格的聊天首页。
它不是完整聊天业务页，而是一个“聊天入口 + 欢迎页 + 会话侧边栏 + 输入框”的界面还原。

用户打开页面 ->
看到左侧会话栏、中间欢迎区、底部输入栏。

左侧会话栏 ->
负责展示聊天/收藏 tab、搜索框、今天/昨天的会话列表，以及底部用户操作按钮。

中间欢迎区 ->
负责展示 ChatGPT Plus、示例、能力和限制。

底部输入栏 ->
负责输入消息、新建聊天，以及接收欢迎区示例卡片填入的 prompt。


2. 核心数据有哪些

activeTab
用户点击“聊天 / 收藏”tab ->
activeTab 改变 ->
tab 的选中样式跟着变化。
目前它只控制 UI 选中态，还没有切换真实数据源。

activeConversation
用户点击左侧某条会话 ->
activeConversation 变成这条会话的 id ->
这条会话显示为选中状态。

draft
用户在底部输入框输入文字 ->
draft 跟着变化。

用户点击欢迎区示例卡片 ->
示例内容写入 draft ->
底部输入框显示这段内容。

用户点击“新建聊天” ->
draft 被清空。

search
用户在左侧搜索框输入关键词 ->
search 改变 ->
今天/昨天的会话列表根据关键词过滤。

todayItems
表示“今天”的会话列表。
页面渲染 ->
从 i18n 里取当前语言的会话标题 ->
默认显示中文。

yesterdayItems
表示“昨天”的会话列表。
页面渲染 ->
通过 localizeYesterdayItem 转成当前语言下的标题 ->
默认显示中文。

filteredToday / filteredYesterday
用户不搜索 ->
显示完整会话列表。

用户输入搜索关键词 ->
只显示标题中包含关键词的会话。


3. 每个方法在做什么

filterItems
用户输入搜索关键词 ->
filterItems 拿关键词匹配会话标题 ->
返回匹配到的会话。

用户清空搜索框 ->
filterItems 发现没有关键词 ->
返回完整列表。

localizeYesterdayItem
页面准备展示“昨天”的会话 ->
localizeYesterdayItem 根据会话 id 找到 i18n 文案 ->
把标题换成当前语言。

同时它会把原来可能乱码的 emoji 替换成稳定短文本，比如 AI、CAT、OK。

resetDraft
用户点击“新建聊天” ->
resetDraft 清空输入框 ->
当前选中会话回到默认的 AI 能力。

sendMessage
用户点击发送按钮 ->
sendMessage 接收输入框里的消息。

目前它只是保留输入内容，没有真正请求后端。
后续接聊天 API 时，这里就是发送入口。

usePrompt
用户点击欢迎区示例卡片 ->
usePrompt 拿到示例文字 ->
去掉外层引号 ->
填入底部输入框。


4. 用户操作流程

用户打开页面 ->
进入 ChatGPT 欢迎页 ->
左侧默认选中“聊天”tab ->
默认选中“AI 能力”会话。

用户点击“聊天 / 收藏”tab ->
tab 选中态变化 ->
目前不切换真实数据。

用户点击搜索框 ->
搜索框进入 focus 状态 ->
视觉上变亮。

用户输入搜索关键词 ->
search 更新 ->
会话列表重新过滤 ->
只显示匹配的会话。

用户点击某条会话 ->
activeConversation 更新 ->
被点击的会话变成选中状态。

用户点击欢迎区示例卡片 ->
示例文字填入底部输入框 ->
发送按钮变成可点击。

用户在底部输入框输入文字 ->
draft 更新 ->
发送按钮可用。

用户清空输入框 ->
draft 为空 ->
发送按钮禁用。

用户点击发送按钮 ->
触发 sendMessage ->
当前还没有真正发请求。

用户点击“新建聊天” ->
触发 resetDraft ->
输入框清空 ->
左侧选中会话回到默认会话。

用户点击关闭、语音、图片、用户等按钮 ->
目前主要是视觉态和基础按钮态 ->
还没有绑定真实业务动作。
-->
<script setup lang="ts">
import {
  ArrowDown,
  Bell,
  Close,
  Cpu,
  EditPen,
  Search,
  Sunny,
  Sunrise,
  User,
  Van
} from "@element-plus/icons-vue";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import ChatComposer from "../components/ChatComposer.vue";
import ChatLogo from "../components/ChatLogo.vue";
import ConversationList, { type ConversationItem } from "../components/ConversationList.vue";
import IconButton from "../components/IconButton.vue";
import MessageList from "../components/MessageList.vue";
import SidebarTabs from "../components/SidebarTabs.vue";
import WelcomePanel from "../components/WelcomePanel.vue";
import { generateMessageId, streamChat, uploadAsset } from "../services/api";
import type { ChatAttachment, ChatMessage } from "../types/api";

const activeTab = ref<"chats" | "saved">("chats");
const activeConversation = ref("ai-capabilities");
const draft = ref("");
const search = ref("");
const { t } = useI18n();

// 新增：消息列表状态管理
const messages = ref<ChatMessage[]>([]);
const isStreaming = ref(false);
const errorMessage = ref("");
const sessionId = ref("");

const todayItems = computed<ConversationItem[]>(() => [
  { id: "ai-capabilities", title: t("sidebar.conversations.aiCapabilities"), icon: Cpu },
  { id: "sunrise-time", title: t("sidebar.conversations.sunriseTime"), icon: Sunrise },
  { id: "matheran-travel", title: t("sidebar.conversations.matheranTravel"), icon: Van },
  { id: "help-assignment", title: t("sidebar.conversations.helpAssignment"), icon: EditPen }
]);

const yesterdayItems = computed<ConversationItem[]>(() => [
  { id: "slr-film", title: "SLR Film Cameras", emoji: "🤖" },
  { id: "quadratic", title: "Quadratic Function Plot", emoji: "😺" },
  { id: "toyota-poetry", title: "Toyota Names Poetry", emoji: "😉" }
]);

const filteredToday = computed(() => filterItems(todayItems.value));
const filteredYesterday = computed(() => filterItems(yesterdayItems.value.map(localizeYesterdayItem)));

// 页面展示“昨天”的会话前，会先进这里。
// 用户看到列表 -> 标题已经根据当前语言替换好；乱码 emoji 也被替换成稳定短文本。
function localizeYesterdayItem(item: ConversationItem): ConversationItem {
  const titleById: Record<string, string> = {
    quadratic: t("sidebar.conversations.quadratic"),
    "slr-film": t("sidebar.conversations.slrFilm"),
    "toyota-poetry": t("sidebar.conversations.toyotaPoetry")
  };
  return {
    ...item,
    emoji: item.id === "slr-film" ? "AI" : item.id === "quadratic" ? "CAT" : "OK",
    title: titleById[item.id] ?? item.title
  };
}

// 用户在搜索框输入关键词 -> 这个方法用关键词匹配会话标题。
// 有关键词 -> 只返回匹配项；没关键词 -> 返回完整列表。
function filterItems(items: ConversationItem[]) {
  const keyword = search.value.trim().toLowerCase();
  if (!keyword) {
    return items;
  }
  return items.filter((item) => item.title.toLowerCase().includes(keyword));
}

// 用户点击“新建聊天” -> 清空底部输入框，并把左侧选中会话切回默认会话。
// 新增：同时清空消息列表和 sessionId
function resetDraft() {
  draft.value = "";
  activeConversation.value = "ai-capabilities";
  messages.value = [];
  sessionId.value = "";
  errorMessage.value = "";
}

function buildAttachmentCommand(kind: string, savedPath: string, promptText: string) {
  const prefixByKind: Record<string, string> = {
    audio: "/audio-file",
    file: "/file-path",
    image: "/image-file",
    video: "/video-file"
  };
  const prefix = prefixByKind[kind] ?? "/file-path";
  return `${prefix} ${savedPath}${promptText ? `|${promptText}` : ""}`;
}

function buildAttachmentCommands(uploadedFiles: UploadedFile[], promptText: string) {
  return uploadedFiles
    .map((item, index) => {
      const prompt = index === uploadedFiles.length - 1 ? promptText : "";
      return buildAttachmentCommand(item.response.inferred_kind, item.response.saved_path, prompt);
    })
    .join("\n");
}

type UploadedFile = {
  file: File;
  previewUrl?: string;
  response: Awaited<ReturnType<typeof uploadAsset>>;
};

async function uploadPendingFiles(files: File[], promptText: string): Promise<UploadedFile[]> {
  const uploadedFiles: UploadedFile[] = [];

  try {
    for (const file of files) {
      const previewUrl = file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined;
      const response = await uploadAsset({
        file,
        kind: "auto",
        prompt: promptText,
        session_id: sessionId.value || undefined,
        user_name: "web-user",
        session_title: "API Session"
      });

      sessionId.value = response.session_id;
      uploadedFiles.push({ file, previewUrl, response });
    }
  } catch (error) {
    for (const item of uploadedFiles) {
      if (item.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
      }
    }
    throw error;
  }

  return uploadedFiles;
}

function toChatAttachments(uploadedFiles: UploadedFile[]): ChatAttachment[] {
  return uploadedFiles.map(({ file, previewUrl, response }) => ({
    assetId: response.trace_id,
    fileName: response.original_name || file.name,
    kind: response.inferred_kind,
    previewUrl,
    savedPath: response.saved_path,
    url: response.download_url,
    downloadUrl: response.download_url
  }));
}

/**
 * 改造：用户点击发送按钮 -> 调用后端流式 API
 * 
 * 流程：
 * 1. 验证输入和状态
 * 2. 添加 user 消息到列表
 * 3. 创建 assistant 消息占位符
 * 4. 调用后端流式接口
 * 5. 逐块追加 assistant 消息内容
 * 6. 处理元数据（session_id）和错误
 * 7. 完成后清空输入框
 */
async function sendMessage(message: string, files: File[] = []) {
  const promptText = message.trim().replace(/\|/g, " ");

  // 防止重复发送和空消息
  if (isStreaming.value || (!promptText && files.length === 0)) {
    return;
  }

  // 清空前一个错误信息
  errorMessage.value = "";
  isStreaming.value = true;

  try {
    const uploadedFiles = files.length ? await uploadPendingFiles(files, promptText) : [];
    const attachments = toChatAttachments(uploadedFiles);
    const backendMessage = uploadedFiles.length ? buildAttachmentCommands(uploadedFiles, promptText) : promptText;
    const userMessage = promptText;

    // 1. 添加 user 消息到列表
    const userMsgId = generateMessageId();
    messages.value.push({
      id: userMsgId,
      role: "user",
      content: userMessage,
      attachments
    });

    // 2. 创建 assistant 消息占位符
    const assistantMsgId = generateMessageId();
    messages.value.push({
      id: assistantMsgId,
      role: "assistant",
      content: ""
    });

    // 3. 调用后端流式接口
    let rawAssistantText = "";
    for await (const event of streamChat({
      message: backendMessage,
      session_id: sessionId.value || undefined,
      user_name: "web-user",
      session_title: "API Session"
    })) {
      if (event.type === "metadata") {
        // 保存 session_id，后续请求会复用
        sessionId.value = event.session_id;
      } else if (event.type === "answer_delta") {
        // 修复：后端返回的是 answer_delta，字段是 delta
        const assistantMsg = messages.value.find((m) => m.id === assistantMsgId);
        if (assistantMsg) {
          console.debug("stream answer_delta", JSON.stringify(event.delta));
          rawAssistantText += event.delta;
          assistantMsg.content = rawAssistantText;
        }
      } else if (event.type === "done") {
        const assistantMsg = messages.value.find((m) => m.id === assistantMsgId);
        if (assistantMsg) {
          const finalAnswer = event.answer ?? rawAssistantText;
          console.debug("stream done answer", JSON.stringify(finalAnswer));
          assistantMsg.content = finalAnswer;
        }
        break;
      } else if (event.type === "error") {
        //错误
        throw new Error(event.message || "Unknown error");
      }
    }
  } catch (err) {
    // 6. 捕获错误并显示
    const errorMsg = err instanceof Error ? err.message : "Failed to send message";
    errorMessage.value = errorMsg;
    console.error("Send message error:", err);
  } finally {
    // 7. 完成后清空输入框和流式标记
    isStreaming.value = false;
    draft.value = "";
  }
}

// 用户点击欢迎区示例卡片 -> 示例文字进入这里。
// 去掉外层引号后写入 draft，底部输入框就会显示这段提示词。
function usePrompt(prompt: string) {
  draft.value = prompt.replace(/"/g, "");
}
</script>

<style scoped>
.chat-redesign-page {
  display: flex;
  height: 100vh;
}

.chat-sidebar {
  display: flex;
  flex-direction: column;
  width: 260px;
  border-right: 1px solid #e5e5e5;
  background-color: #fff;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  position: relative;
}

/* 欢迎区放在顶部，有消息时隐藏 */
.chat-main > :first-child {
  flex: 1;
  overflow-y: auto;
}

/* 错误提示样式 */
.chat-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 0 16px;
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 14px;
  animation: slideDown 0.3s ease-out;
}

.chat-error__icon {
  flex-shrink: 0;
  font-size: 16px;
}

.chat-error__text {
  flex: 1;
  word-break: break-word;
}

.chat-error__close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #856404;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.chat-error__close:hover {
  opacity: 0.7;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
