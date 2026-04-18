<template>
  <form class="chat-composer" @submit.prevent="submit">
<!--    <button class="chat-composer__new" type="button" @click="$emit('newChat')">-->
<!--      <CirclePlusFilled />-->
<!--      <span>{{ t("composer.newChat") }}</span>-->
<!--    </button>-->

    <div class="chat-composer__box">
      <div v-if="pendingFiles.length" class="chat-composer__pending" :aria-label="t('composer.pendingFiles')">
        <article v-for="item in pendingFiles" :key="item.id" class="pending-file">
          <img
            v-if="isImageFile(item)"
            class="pending-file__preview"
            :alt="item.name"
            :src="item.previewUrl"
          />
          <span v-else class="pending-file__icon">FILE</span>
          <!--如果是图片就不展示图片名称；如果是文件就展示源文件名称；文件类型统一不展示-->
          <span class="pending-file__meta">
            <span class="pending-file__name">{{ item.name }}</span>
<!--            <span class="pending-file__type">{{ item.type || t("composer.unknownFile") }}</span>-->
          </span>
          <button
            class="pending-file__remove"
            type="button"
            :aria-label="t('composer.removeFile')"
            @click="removePendingFile(item.id)"
          >
            ×
          </button>
        </article>
      </div>

      <div class="chat-composer__row">
        <div class="chat-composer__upload">
          <button
            class="chat-composer__plus"
            type="button"
            :aria-expanded="isUploadMenuOpen"
            :aria-label="t('composer.openUploadMenu')"
            @click="toggleUploadMenu"
          >
            <Plus />
          </button>
          <div v-if="isUploadMenuOpen" class="chat-composer__menu" role="menu">
            <button class="chat-composer__menu-item" type="button" role="menuitem" @click="chooseFiles">
              <Picture />
              <span>{{ t("composer.addPhotoAndFile") }}</span>
            </button>
            <button class="chat-composer__menu-item" type="button" role="menuitem" @click="closeUploadMenu">
              <Clock />
              <span>{{ t("composer.recentFiles") }}</span>
            </button>
          </div>
        </div>

        <input ref="fileInput" type="file" hidden multiple @change="onFileChange" />

        <label class="chat-composer__field">
          <Search class="chat-composer__search" />
          <input
            v-model="draft"
            :aria-label="t('composer.typeMessage')"
            :placeholder="t('composer.typeMessage')"
            type="text"
            @focus="$emit('focus')"
          />
        </label>

        <div class="chat-composer__actions">
          <IconButton :icon="Microphone" :label="t('composer.voiceInput')" size="lg" />
          <IconButton
            :disabled="!canSubmit"
            :icon="Promotion"
            :label="t('composer.sendMessage')"
            size="lg"
            @click="submit"
          />
        </div>
      </div>
    </div>
  </form>
</template>

<script setup lang="ts">
import {Clock, Microphone, Picture, Plus, Promotion, Search } from "@element-plus/icons-vue";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import IconButton from "./IconButton.vue";

type PendingFile = {
  id: string;
  file: File;
  name: string;
  type: string;
  previewUrl?: string;
};

const props = defineProps<{
  modelValue: string;
  isLoading?: boolean;
}>();

const emit = defineEmits<{
  focus: [];
  newChat: [];
  send: [string, File[]];
  "update:modelValue": [string];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const draft = ref(props.modelValue);
const pendingFiles = ref<PendingFile[]>([]);
const isUploadMenuOpen = ref(false);
const { t } = useI18n();

const canSubmit = computed(() => !props.isLoading && (draft.value.trim().length > 0 || pendingFiles.value.length > 0));

function toggleUploadMenu() {
  isUploadMenuOpen.value = !isUploadMenuOpen.value;
}

function closeUploadMenu() {
  isUploadMenuOpen.value = false;
}

function chooseFiles() {
  closeUploadMenu();
  fileInput.value?.click();
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null;
  const files = Array.from(target?.files ?? []);

  if (files.length) {
    pendingFiles.value.push(
      ...files.map((file) => ({
        id: `${file.name}_${file.lastModified}_${Math.random().toString(36).slice(2, 8)}`,
        file,
        name: file.name,
        type: file.type,
        previewUrl: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined
      }))
    );
  }

  if (target) {
    target.value = "";
  }
}

function removePendingFile(id: string) {
  const item = pendingFiles.value.find((file) => file.id === id);
  if (item?.previewUrl) {
    URL.revokeObjectURL(item.previewUrl);
  }
  pendingFiles.value = pendingFiles.value.filter((file) => file.id !== id);
}

function isImageFile(item: PendingFile): boolean {
  return item.type.startsWith("image/") && Boolean(item.previewUrl);
}

function clearPendingFiles() {
  for (const item of pendingFiles.value) {
    if (item.previewUrl) {
      URL.revokeObjectURL(item.previewUrl);
    }
  }
  pendingFiles.value = [];
}

watch(
  () => props.modelValue,
  (value) => {
    draft.value = value;
  }
);

watch(draft, (value) => {
  emit("update:modelValue", value);
});

onBeforeUnmount(clearPendingFiles);

function submit() {
  if (!canSubmit.value) {
    return;
  }
  const files = pendingFiles.value.map((item) => item.file);
  emit("send", draft.value.trim(), files);
  clearPendingFiles();
}
</script>

<style scoped>
.chat-composer {
  display: flex;
  align-items: stretch;
  gap: 12px;
  width: min(760px, calc(100% - 48px));
  margin: 0 auto 24px;
}

.chat-composer__new {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-end;
  height: 46px;
  padding: 0 14px;
  border: 1px solid #d9dde3;
  border-radius: 8px;
  background: #fff;
  color: #30343b;
  font-size: 14px;
  cursor: pointer;
}

.chat-composer__new svg {
  width: 18px;
  height: 18px;
}

.chat-composer__box {
  flex: 1;
  min-width: 0;
  border: 1px solid #d9dde3;
  border-radius: 36px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(28, 35, 48, 0.08);
}

.chat-composer__pending {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 10px 12px 0;
}

.pending-file {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  flex: 0 0 220px;
  max-width: 220px;
  padding: 8px;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  background: #f7f8fa;
}

.pending-file__preview,
.pending-file__icon {
  width: 38px;
  height: 38px;
  border-radius: 6px;
}

.pending-file__preview {
  object-fit: cover;
  background: #eceff3;
}

.pending-file__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e9edf2;
  color: #4c5563;
  font-size: 10px;
  font-weight: 700;
}

.pending-file__meta {
  display: grid;
  min-width: 0;
}

.pending-file__name,
.pending-file__type {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pending-file__name {
  color: #20242b;
  font-size: 13px;
  font-weight: 600;
}

.pending-file__type {
  color: #6d7480;
  font-size: 12px;
}

.pending-file__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #6d7480;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.pending-file__remove:hover {
  background: #e6e9ee;
  color: #20242b;
}

.chat-composer__row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 54px;
  padding: 6px 8px;
}

.chat-composer__upload {
  position: relative;
  flex: 0 0 auto;
}

.chat-composer__plus {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #30343b;
  cursor: pointer;
}

.chat-composer__plus:hover {
  background: #f0f2f5;
}

.chat-composer__plus svg {
  width: 20px;
  height: 20px;
}

.chat-composer__menu {
  position: absolute;
  left: 0;
  bottom: calc(100% + 8px);
  z-index: 10;
  display: grid;
  width: 220px;
  padding: 6px;
  border: 1px solid #dfe3e8;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(28, 35, 48, 0.16);
}

.chat-composer__menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #20242b;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.chat-composer__menu-item:hover {
  background: #f0f2f5;
}

.chat-composer__menu-item svg {
  width: 18px;
  height: 18px;
}

.chat-composer__field {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.chat-composer__search {
  width: 18px;
  height: 18px;
  color: #8b929d;
}

.chat-composer__field input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: none;
  color: #20242b;
  font-size: 15px;
}
.chat-composer__field input::placeholder {
  color: #8b929d;
}

.chat-composer__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}

@media (max-width: 768px) {
  .chat-composer {
    width: calc(100% - 24px);
    margin-bottom: 16px;
  }

  .chat-composer__new span {
    display: none;
  }
}
</style>
