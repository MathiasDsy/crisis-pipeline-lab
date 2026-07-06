<script setup lang="ts">
import { ref, computed } from 'vue'

export interface SelectItem {
  id:        string
  label:     string
  sublabel?: string
  disabled?: boolean
}

const props = defineProps<{
  label:     string
  items:     SelectItem[]
  selected:  Set<string>
  disabled?: boolean
  single?:   boolean
}>()

const emit = defineEmits<{
  toggle:    [id: string]
  selectAll: []
}>()

const isOpen = ref(false)

const selectedCount = computed(() => props.selected.size)

const allSelected = computed(() =>
  props.items.filter((i) => !i.disabled).length > 0 &&
  props.items.filter((i) => !i.disabled).every((i) => props.selected.has(i.id)),
)

const summaryLabel = computed(() => {
  if (selectedCount.value === 0) return props.single ? 'Select…' : 'None selected'
  if (selectedCount.value === 1) {
    const item = props.items.find((i) => props.selected.has(i.id))
    return item?.label ?? '1 selected'
  }
  return `${selectedCount.value} selected`
})

function onToggle(id: string) {
  emit('toggle', id)
  if (props.single) isOpen.value = false
}
</script>

<template>
  <div class="msd" :class="{ 'msd--open': isOpen, 'msd--disabled': disabled }">
    <span class="msd-legend">{{ label }}</span>

    <!-- Trigger -->
    <button
      class="msd-trigger"
      :disabled="disabled"
      @click="isOpen = !isOpen"
    >
      <span class="msd-summary" :class="{ 'msd-summary--empty': selectedCount === 0 }">
        {{ summaryLabel }}
      </span>
      <svg
        class="msd-chevron"
        width="12" height="12" viewBox="0 0 12 12" fill="none"
      >
        <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- Dropdown body -->
    <div v-if="isOpen" class="msd-body">
      <div v-if="!single" class="msd-actions">
        <button
          class="btn btn-ghost btn-sm"
          :disabled="disabled || items.length === 0"
          @click="emit('selectAll')"
        >
          {{ allSelected ? 'Deselect all' : 'Select all' }}
        </button>
      </div>

      <div v-if="items.length === 0" class="msd-empty">
        <span class="text-xs text-muted">No items available</span>
      </div>

      <ul v-else class="msd-list">
        <li
          v-for="item in items"
          :key="item.id"
        >
          <label
            class="msd-item"
            :class="{
              'msd-item--on':       selected.has(item.id),
              'msd-item--disabled': item.disabled,
            }"
          >
            <input
              :type="single ? 'radio' : 'checkbox'"
              class="msd-check"
              :checked="selected.has(item.id)"
              :disabled="disabled || item.disabled"
              @change="onToggle(item.id)"
            />
            <div class="msd-item-text">
              <span class="msd-item-label">{{ item.label }}</span>
              <span v-if="item.sublabel" class="msd-item-sub text-xs text-muted truncate">
                {{ item.sublabel }}
              </span>
            </div>
          </label>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.msd {
  position: relative;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.msd--disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* Fieldset-style floating label */
.msd-legend {
  position: absolute;
  top: -9px;
  left: 12px;
  padding: 0 var(--sp-1);
  background: var(--color-surface);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  line-height: 1;
  pointer-events: none;
}

/* Trigger row */
.msd-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-2) var(--sp-3);
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-primary);
  border-radius: var(--radius-lg);
  transition: background var(--t-fast);
}

.msd-trigger:hover {
  background: var(--color-surface-elevated);
}

.msd-summary {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-accent);
}

.msd-summary--empty {
  color: var(--color-text-muted);
  font-weight: var(--fw-normal);
}

.msd-chevron {
  color: var(--color-text-muted);
  transition: transform var(--t-base);
  flex-shrink: 0;
}

.msd--open .msd-chevron {
  transform: rotate(180deg);
}

/* Dropdown body */
.msd-body {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--sp-2) var(--sp-2) var(--sp-2);
}

.msd-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--sp-1);
}

.msd-empty {
  padding: var(--sp-2) var(--sp-2);
}

.msd-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.msd-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-2);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--t-fast), border-color var(--t-fast);
}

.msd-item:hover:not(.msd-item--disabled) {
  background: var(--color-surface-elevated);
}

.msd-item--on {
  background: var(--color-accent-subtle);
  border-color: rgba(59, 130, 246, 0.2);
}

.msd-item--disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.msd-check {
  accent-color: var(--color-accent);
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  cursor: pointer;
}

.msd-item--disabled .msd-check { cursor: not-allowed; }

.msd-item-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  min-width: 0;
}

.msd-item-label {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  line-height: 1.3;
}
</style>
