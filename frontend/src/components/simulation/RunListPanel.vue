<script setup lang="ts">
import { computed } from 'vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import type { Run } from '@/types/run'
import type { Dataset } from '@/types/dataset'
import type { PipelineConfig } from '@/types/pipeline'

const props = defineProps<{
  runs:          Run[]
  datasets:      Dataset[]
  pipelines:     PipelineConfig[]
  selectedRunId: string | null
  isLoading:     boolean
}>()

const emit = defineEmits<{
  select:  [runId: string]
  newRun:  []
}>()

function datasetName(id: string | null) {
  if (!id) return 'Unknown dataset'
  return props.datasets.find((d) => d.id === id)?.name ?? id.slice(0, 8)
}

function pipelineName(id: string | null) {
  if (!id) return 'Fixed pipeline'
  return props.pipelines.find((p) => p.id === id)?.name ?? id.slice(0, 8)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

const sortedRuns = computed(() =>
  [...props.runs].sort(
    (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
  ),
)
</script>

<template>
  <aside class="run-list-panel">
    <div class="panel-header">
      <h2 class="panel-title">Simulations</h2>
      <button class="btn btn-primary btn-sm" @click="emit('newRun')">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <line x1="6" y1="1" x2="6" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="1" y1="6" x2="11" y2="6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        New run
      </button>
    </div>

    <div class="panel-body">
      <!-- Loading skeleton -->
      <template v-if="isLoading">
        <div v-for="n in 4" :key="n" class="run-skeleton" />
      </template>

      <!-- Empty -->
      <div v-else-if="sortedRuns.length === 0" class="empty-state">
        <span class="empty-state-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </span>
        <p class="text-sm">No runs yet.</p>
        <p class="text-xs text-muted">Click "New run" to start.</p>
      </div>

      <!-- Run list -->
      <ul v-else class="run-items">
        <li
          v-for="run in sortedRuns"
          :key="run.id"
          class="run-item"
          :class="{ 'run-item--active': run.id === selectedRunId }"
          @click="emit('select', run.id)"
        >
          <div class="run-item-top">
            <span class="run-name truncate">
              {{ run.name || datasetName(run.dataset_id) }}
            </span>
            <StatusBadge :status="run.status" />
          </div>
          <div class="run-item-sub">
            <span class="truncate text-xs text-muted">{{ pipelineName(run.pipeline_config_id) }}</span>
            <span class="text-xs text-muted">{{ formatDate(run.started_at) }}</span>
          </div>
        </li>
      </ul>
    </div>
  </aside>
</template>

<style scoped>
.run-list-panel {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.panel-header {
  padding: var(--sp-4) var(--sp-4) var(--sp-3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.panel-title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-2);
}

.run-items {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.run-item {
  padding: var(--sp-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--t-fast);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.run-item:hover {
  background: var(--color-surface-elevated);
}

.run-item--active {
  background: var(--color-accent-subtle);
}

.run-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.run-item-sub {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.run-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  min-width: 0;
}

/* Skeleton */
.run-skeleton {
  height: 56px;
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  margin-bottom: 2px;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50%       { opacity: 0.3; }
}
</style>
