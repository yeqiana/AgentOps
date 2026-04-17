<template>
  <section class="conversation-list" :aria-label="title">
    <div class="conversation-list__header">{{ title }}</div>
    <button
      v-for="item in items"
      :key="item.id"
      class="conversation-list__row"
      :class="{ 'conversation-list__row--active': modelValue === item.id }"
      type="button"
      @click="$emit('update:modelValue', item.id)"
    >
      <span class="conversation-list__icon" :class="{ 'conversation-list__icon--emoji': item.emoji }">
        <component :is="item.icon" v-if="item.icon" />
        <span v-else>{{ item.emoji }}</span>
      </span>
      <span class="conversation-list__title">{{ item.title }}</span>
    </button>
  </section>
</template>

<script setup lang="ts">
import type { Component } from "vue";

export interface ConversationItem {
  emoji?: string;
  icon?: Component;
  id: string;
  title: string;
}

defineProps<{
  items: ConversationItem[];
  modelValue: string;
  title: string;
}>();

defineEmits<{
  "update:modelValue": [string];
}>();
</script>
