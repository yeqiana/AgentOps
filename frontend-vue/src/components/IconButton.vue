<template>
  <button
    class="icon-button"
    :class="[`icon-button--${size}`, { 'icon-button--selected': selected }]"
    :aria-label="label"
    :disabled="disabled"
    type="button"
    @click="handleClick"
  >
    <component :is="icon" />
  </button>
</template>

<script setup lang="ts">
import type { Component } from "vue";

const props = withDefaults(
  defineProps<{
    disabled?: boolean;
    icon: Component;
    label: string;
    selected?: boolean;
    size?: "sm" | "md" | "lg";
  }>(),
  {
    disabled: false,
    selected: false,
    size: "md"
  }
);

const emit = defineEmits<{
  click: [];
}>();

function handleClick() {
  if (!props.disabled) {
    emit('click');
  }
}
</script>
