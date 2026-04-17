<template>
  <form class="chat-composer" @submit.prevent="submit">
    <button class="chat-composer__new" type="button" @click="$emit('newChat')">
      <CirclePlusFilled />
      <span>{{ t("composer.newChat") }}</span>
    </button>

    <IconButton :icon="Microphone" :label="t('composer.voiceInput')" size="lg" />
    <IconButton :icon="Picture" :label="t('composer.attachImage')" size="lg" @click="openFilePicker" />
    <input ref="fileInput" type="file" accept="image/*" hidden @change="onFileChange" />

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

    <IconButton :disabled="!draft.trim() || isLoading" :icon="Promotion" :label="t('composer.sendMessage')" size="lg" />
  </form>
</template>

<script setup lang="ts">
import { CirclePlusFilled, Microphone, Picture, Promotion, Search } from "@element-plus/icons-vue";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import IconButton from "./IconButton.vue";

const props = defineProps<{
  modelValue: string;
  isLoading?: boolean;
}>();

const emit = defineEmits<{
  focus: [];
  newChat: [];
  upload: [File];
  send: [string];
  "update:modelValue": [string];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const draft = ref(props.modelValue);
const { t } = useI18n();

function openFilePicker() {
  fileInput.value?.click();
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null;
  const file = target?.files?.[0];

  if (file) {
    emit('upload', file);
  }

  if (target) {
    target.value = '';
  }
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

function submit() {
  const message = draft.value.trim();
  if (!message) {
    return;
  }
  emit("send", message);
}
</script>
