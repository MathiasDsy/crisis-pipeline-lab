<script setup lang="ts">
import { computed } from 'vue'
import type { Model } from '@/types/model'

const props = defineProps<{
  label:     string
  models:    Model[]
  selected:  Set<string>
  disabled?: boolean
}>()

const emit = defineEmits<{
  toggle:    [key: string]
  selectAll: []
}>()

const allSelected = computed(() =>
  props.models.length > 0 && props.models.every((m) => props.selected.has(m.model_key)),
)
</script>

<template>
  <div class="step-picker">
    <div class="picker-header">
      <span class="section-label">{{ label }}</span>
      <div class="picker-header-right">
        <span class="text-xs text-muted">{{ selected.size }}/{{ models.length }}</span>
        <button
          class="btn btn-ghost btn-sm"
          :disabled="disabled || models.length === 0"
          @click="emit('selectAll')"
        >
          {{ allSelected ? 'Deselect all' : 'Select all' }}
        </button>
      </div>
    </div>

    <div v-if="models.length === 0" class="picker-empty">
      <span class="text-xs text-muted">No models available for this step</span>
    </div>

    <div v-else class="picker-items">
      <label
        v-for="model in models"
        :key="model.model_key"
        class="model-item"
        :class="{
          'model-item--selected':    selected.has(model.model_key),
          'model-item--unavailable': !model.is_available,
        }"
      >
        <input
          type="checkbox"
          class="model-checkbox"
          :checked="selected.has(model.model_key)"
          :disabled="disabled || !model.is_available"
          @change="emit('toggle', model.model_key)"
        />
        <div class="model-info">
          <span class="text-sm font-medium">{{ model.name }}</span>
          <span class="text-xs text-muted font-mono">{{ model.model_key }}</span>
        </div>
        <span v-if="!model.is_available" class="badge badge-muted" style="font-size:10px">
          unavailable
        </span>
      </label>
    </div>
  </div>
</template>

<style scoped>
.step-picker {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.picker-header-right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.picker-empty { padding: var(--sp-1) 0; }

.picker-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-2);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--t-fast), border-color var(--t-fast);
}

.model-item:hover:not(.model-item--unavailable) {
  background: var(--color-surface-elevated);
}

.model-item--selected {
  background: var(--color-accent-subtle);
  border-color: rgba(59, 130, 246, 0.2);
}

.model-item--unavailable {
  opacity: 0.5;
  cursor: not-allowed;
}

.model-checkbox {
  accent-color: var(--color-accent);
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  cursor: pointer;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}
</style>
