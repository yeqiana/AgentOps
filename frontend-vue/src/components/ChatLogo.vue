<template>
  <div class="chat-logo" :class="{ 'chat-logo--compact': compact }" aria-label="ChatGPT">
    <span class="chat-logo__mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
    <span class="chat-logo__text">ChatGPT</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  compact?: boolean;
}>();
</script>
