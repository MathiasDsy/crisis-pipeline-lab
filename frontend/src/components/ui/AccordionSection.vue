<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  title:        string
  badge?:       string
  initialOpen?: boolean
}>()

const isOpen = ref(props.initialOpen ?? true)
</script>

<template>
  <div class="accordion" :class="{ 'accordion--open': isOpen }">
    <button class="accordion-trigger" @click="isOpen = !isOpen">
      <span class="accordion-title">{{ title }}</span>
      <div class="accordion-right">
        <span v-if="badge" class="accordion-badge">{{ badge }}</span>
        <svg
          class="accordion-chevron"
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
        >
          <path
            d="M3 5l4 4 4-4"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
    </button>

    <div v-show="isOpen" class="accordion-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.accordion {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface);
}

.accordion-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-primary);
  transition: background var(--t-fast);
  text-align: left;
}

.accordion-trigger:hover {
  background: var(--color-surface-elevated);
}

.accordion-title {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.accordion-right {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.accordion-badge {
  font-size: var(--text-xs);
  font-weight: var(--fw-medium);
  color: var(--color-accent);
  background: var(--color-accent-subtle);
  padding: 1px 6px;
  border-radius: 999px;
}

.accordion-chevron {
  color: var(--color-text-muted);
  transition: transform var(--t-base);
  flex-shrink: 0;
}

.accordion--open .accordion-chevron {
  transform: rotate(180deg);
}

.accordion-body {
  padding: 0 var(--sp-4) var(--sp-4);
  border-top: 1px solid var(--color-border-subtle);
}
</style>
