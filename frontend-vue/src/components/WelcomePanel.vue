<template>
  <main class="welcome-panel" aria-labelledby="welcome-title">
    <div class="welcome-panel__brand">
      <ChatLogo />
      <span class="welcome-panel__tag">{{ t("welcome.plan") }}</span>
    </div>

    <div class="welcome-panel__grid">
      <section v-for="column in columns" :key="column.title" class="welcome-column">
        <div class="welcome-column__heading">
          <component :is="column.icon" />
          <h2 :id="column.title === 'Examples' ? 'welcome-title' : undefined">
            {{ column.title }}
          </h2>
        </div>
        <button
          v-for="entry in column.entries"
          :key="entry"
          class="welcome-card"
          type="button"
          @click="$emit('selectPrompt', entry)"
        >
          {{ entry }}
        </button>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ChatLineRound, MagicStick, Warning } from "@element-plus/icons-vue";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import ChatLogo from "./ChatLogo.vue";

defineEmits<{
  selectPrompt: [string];
}>();

const { t, tm } = useI18n();

function translatedList(key: string) {
  return (tm(key) as unknown[]).map((entry) => String(entry));
}

const columns = computed(() => [
  {
    title: t("welcome.columns.examples.title"),
    icon: ChatLineRound,
    entries: translatedList("welcome.columns.examples.entries")
  },
  {
    title: t("welcome.columns.capabilities.title"),
    icon: MagicStick,
    entries: translatedList("welcome.columns.capabilities.entries")
  },
  {
    title: t("welcome.columns.limitations.title"),
    icon: Warning,
    entries: translatedList("welcome.columns.limitations.entries")
  }
]);
</script>
