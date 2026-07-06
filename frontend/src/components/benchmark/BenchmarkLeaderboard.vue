<script setup lang="ts">
import type { LeaderboardEntry } from '@/types/benchmark'
import type { Model } from '@/types/model'

const props = defineProps<{
  entries:       LeaderboardEntry[]
  selectedRunId: string | null
  models:        Model[]
}>()

const emit = defineEmits<{
  selectRun: [runId: string]
}>()

function pct(v: number | undefined | null) {
  if (v === undefined || v === null) return '—'
  return `${(v * 100).toFixed(1)}%`
}

function modelName(key: string) {
  return props.models.find((m) => m.model_key === key)?.name ?? key
}

function rankClass(i: number) {
  if (i === 0) return 'rank-gold'
  if (i === 1) return 'rank-silver'
  if (i === 2) return 'rank-bronze'
  return ''
}
</script>

<template>
  <div class="leaderboard">
    <div class="leaderboard-header">
      <h3 class="text-sm font-semibold">Leaderboard</h3>
      <span class="text-xs text-muted">{{ entries.length }} runs · sorted by F1</span>
    </div>

    <div class="table-wrapper">
      <table class="lb-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Classifier</th>
            <th>Extractor</th>
            <th>F1</th>
            <th>Precision</th>
            <th>Recall</th>
            <th>Accuracy</th>
            <th>TP</th>
            <th>FP</th>
            <th>FN</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(e, i) in entries"
            :key="e.run_id"
            class="lb-row"
            :class="{ 'lb-row--selected': e.run_id === selectedRunId, [rankClass(i)]: true }"
            @click="emit('selectRun', e.run_id)"
          >
            <td class="rank-cell"><span class="rank-num">{{ i + 1 }}</span></td>
            <td class="name-cell truncate" :title="e.model_snapshot_json.classifier_model_key">
              {{ modelName(e.model_snapshot_json.classifier_model_key) }}
            </td>
            <td class="name-cell truncate" :title="e.model_snapshot_json.location_model_key">
              {{ modelName(e.model_snapshot_json.location_model_key) }}
            </td>
            <td class="metric-cell f1-cell">{{ pct(e.f1) }}</td>
            <td class="metric-cell">{{ pct(e.precision) }}</td>
            <td class="metric-cell">{{ pct(e.recall) }}</td>
            <td class="metric-cell">{{ pct(e.accuracy) }}</td>
            <td class="center-cell text-xs" style="color:var(--color-success)">{{ e.tp }}</td>
            <td class="center-cell text-xs" style="color:var(--color-error)">{{ e.fp }}</td>
            <td class="center-cell text-xs" style="color:var(--color-warning)">{{ e.fn }}</td>
            <td class="center-cell">
              <span
                class="badge"
                :class="e.status === 'completed' ? 'badge-success'
                      : e.status === 'error'     ? 'badge-error'
                      : 'badge-running'"
              >
                {{ e.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.leaderboard {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.leaderboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.table-wrapper { overflow-x: auto; }

.lb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.lb-table thead tr { border-bottom: 1px solid var(--color-border-subtle); }

.lb-table th {
  padding: var(--sp-2) var(--sp-3);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.lb-row {
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: background var(--t-fast);
}

.lb-row:last-child { border-bottom: none; }
.lb-row:hover { background: var(--color-surface-elevated); }
.lb-row--selected { background: var(--color-accent-subtle); }

.lb-table td {
  padding: var(--sp-2) var(--sp-3);
  white-space: nowrap;
}

.rank-cell { width: 40px; }

.rank-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
}

.rank-gold   .rank-num { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.rank-silver .rank-num { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
.rank-bronze .rank-num { background: rgba(180, 120, 60, 0.2); color: #b47a3c; }

.name-cell   { max-width: 180px; font-weight: var(--fw-medium); }
.center-cell { text-align: center; color: var(--color-text-secondary); }
.metric-cell { text-align: right; font-weight: var(--fw-medium); }
.f1-cell     { color: var(--color-accent); font-size: var(--text-md); }
</style>
