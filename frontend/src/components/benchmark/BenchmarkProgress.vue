<script setup lang="ts">
import type { Benchmark } from '@/types/benchmark'

defineProps<{
  benchmark:      Benchmark
  completedCount: number
  totalCount:     number
  progress:       number
  isRunning:      boolean
}>()

const emit = defineEmits<{
  cancel: []
}>()
</script>

<template>
  <div class="bm-progress">
    <div class="bm-progress-head">
      <div class="bm-progress-title">
        <span v-if="isRunning" class="spinner" />
        <span class="text-sm font-medium">
          {{ isRunning ? 'Running benchmark' : 'Benchmark ' + benchmark.status }}
          — {{ completedCount }}/{{ totalCount }} runs
        </span>
      </div>
      <button v-if="isRunning" class="btn btn-danger btn-sm" @click="emit('cancel')">
        Cancel
      </button>
    </div>

    <div class="progress-track">
      <div class="progress-fill" :style="{ width: `${progress}%` }" />
    </div>

    <span class="text-xs text-muted">{{ Math.round(progress) }}% · {{ benchmark.name }}</span>
  </div>
</template>

<style scoped>
.bm-progress {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.bm-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bm-progress-title {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.progress-track {
  height: 4px;
  background: var(--color-surface-elevated);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 2px;
  transition: width 0.4s ease;
}
</style>
