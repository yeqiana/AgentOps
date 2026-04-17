<template>
  <div class="sidebar-tabs" role="tablist" :aria-label="t('sidebar.tabsLabel')">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      class="sidebar-tabs__item"
      :class="{ 'sidebar-tabs__item--active': modelValue === tab.key }"
      role="tab"
      type="button"
      :aria-selected="modelValue === tab.key"
      @click="$emit('update:modelValue', tab.key)"
    >
      <component :is="tab.icon" class="sidebar-tabs__icon" />
      <span>{{ tab.label }}</span>
      <strong>{{ tab.count }}</strong>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, CollectionTag } from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";

defineProps<{
  modelValue: "chats" | "saved";
}>();

defineEmits<{
  "update:modelValue": ["chats" | "saved"];
}>();

const { t } = useI18n();

const tabs = [
  { key: "chats" as const, label: t("sidebar.tabs.chats"), count: 24, icon: ChatDotRound },
  { key: "saved" as const, label: t("sidebar.tabs.saved"), count: 24, icon: CollectionTag }
];
</script>
