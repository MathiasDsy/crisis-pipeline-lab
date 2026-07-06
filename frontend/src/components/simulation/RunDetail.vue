<script setup lang="ts">
import { ref } from 'vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import RunMap      from './RunMap.vue'
import TweetList   from './TweetList.vue'
import type { Run, RunSummary, RunMetrics } from '@/types/run'
import type { FireEvent } from '@/types/event'
import type { Tweet, StepExecution } from '@/types/tweet'

const props = defineProps<{
  run:          Run
  summary:      RunSummary | null
  metrics:      RunMetrics | null
  events:       FireEvent[]
  tweets:       Tweet[]
  trace:        StepExecution[]
  isLoading:    boolean
  isPolling:    boolean
}>()

const emit = defineEmits<{
  cancel: [runId: string]
}>()

type Tab = 'overview' | 'map' | 'tweets'
const activeTab = ref<Tab>('overview')

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function duration(start: string, end: string | null) {
  if (!end) return '—'
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const s  = Math.round(ms / 1000)
  return s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`
}

function pct(val: number | undefined) {
  if (val === undefined || val === null) return '—'
  return `${(val * 100).toFixed(1)}%`
}
</script>

<template>
  <div class="run-detail">
    <!-- Header -->
    <div class="detail-header">
      <div class="detail-title-row">
        <h2 class="detail-title truncate">
          {{ run.name || run.id.slice(0, 8) }}
        </h2>
        <StatusBadge :status="run.status" />
      </div>

      <div class="detail-meta">
        <span class="text-xs text-muted">Started {{ formatDate(run.started_at) }}</span>
        <span v-if="run.finished_at" class="text-xs text-muted">
          · {{ duration(run.started_at, run.finished_at) }}
        </span>
        <span class="detail-meta-spacer" />
        <button
          v-if="run.status === 'running'"
          class="btn btn-danger btn-sm"
          @click="emit('cancel', run.id)"
        >
          Cancel
        </button>
      </div>
    </div>

    <!-- Loading overlay for running state -->
    <div v-if="isPolling && run.status === 'running'" class="running-banner">
      <span class="spinner" />
      <span class="text-sm">Simulation running — results will appear automatically…</span>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in (['overview', 'map', 'tweets'] as Tab[])"
        :key="tab"
        class="tab"
        :class="{ 'tab--active': activeTab === tab }"
        @click="activeTab = tab"
      >
        {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
      </button>
    </div>

    <!-- Tab content -->
    <div class="tab-content">
      <!-- ── Overview ─────────────────────────────── -->
      <div v-if="activeTab === 'overview'">
        <div v-if="isLoading && !metrics" class="loading-state">
          <span class="spinner" />
          <span class="text-sm text-muted">Loading results…</span>
        </div>

        <template v-else>
          <!-- Metrics cards -->
          <div v-if="metrics" class="metrics-grid">
            <div class="metric-card">
              <div class="metric-value">{{ pct(metrics.precision) }}</div>
              <div class="metric-label">Precision</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">{{ pct(metrics.recall) }}</div>
              <div class="metric-label">Recall</div>
            </div>
            <div class="metric-card metric-card--accent">
              <div class="metric-value">{{ pct(metrics.f1) }}</div>
              <div class="metric-label">F1</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">{{ pct(metrics.accuracy) }}</div>
              <div class="metric-label">Accuracy</div>
            </div>
          </div>

          <!-- Confusion matrix counts -->
          <div v-if="metrics" class="confusion-row">
            <div class="confusion-cell confusion-tp">
              <div class="confusion-val">{{ metrics.tp }}</div>
              <div class="confusion-name">True Positive</div>
            </div>
            <div class="confusion-cell confusion-fp">
              <div class="confusion-val">{{ metrics.fp }}</div>
              <div class="confusion-name">False Positive</div>
            </div>
            <div class="confusion-cell confusion-fn">
              <div class="confusion-val">{{ metrics.fn }}</div>
              <div class="confusion-name">False Negative</div>
            </div>
            <div class="confusion-cell confusion-tn">
              <div class="confusion-val">{{ metrics.tn }}</div>
              <div class="confusion-name">True Negative</div>
            </div>
          </div>

          <!-- Summary stats -->
          <div v-if="summary" class="summary-grid">
            <div class="summary-item">
              <div class="summary-val">{{ summary.tweets_processed }}</div>
              <div class="summary-key">Tweets processed</div>
            </div>
            <div class="summary-item">
              <div class="summary-val">{{ summary.events_created }}</div>
              <div class="summary-key">Events created</div>
            </div>
            <div class="summary-item">
              <div class="summary-val">{{ summary.steps_executed }}</div>
              <div class="summary-key">Steps executed</div>
            </div>
            <div class="summary-item">
              <div class="summary-val" :class="summary.errors > 0 ? 'val-error' : ''">
                {{ summary.errors }}
              </div>
              <div class="summary-key">Errors</div>
            </div>
          </div>

          <div v-if="!metrics && !summary" class="empty-state">
            <p class="text-sm text-muted">No results available yet.</p>
          </div>
        </template>
      </div>

      <!-- ── Map ──────────────────────────────────── -->
      <div v-else-if="activeTab === 'map'">
        <RunMap :events="events" />
      </div>

      <!-- ── Tweets ───────────────────────────────── -->
      <div v-else-if="activeTab === 'tweets'">
        <div v-if="isLoading && tweets.length === 0" class="loading-state">
          <span class="spinner" />
          <span class="text-sm text-muted">Loading tweets…</span>
        </div>
        <TweetList v-else :tweets="tweets" :trace="trace" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.run-detail {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ──────────────────────────────────────────────── */
.detail-header {
  padding: var(--sp-4) var(--sp-6);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.detail-title-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}

.detail-title {
  font-size: var(--text-xl);
  font-weight: var(--fw-semibold);
  min-width: 0;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.detail-meta-spacer { flex: 1; }

/* ── Running banner ──────────────────────────────────────── */
.running-banner {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-6);
  background: var(--color-running-subtle);
  border-bottom: 1px solid rgba(167, 139, 250, 0.2);
  color: var(--color-running);
  flex-shrink: 0;
}

/* ── Tabs ────────────────────────────────────────────────── */
.tabs {
  display: flex;
  gap: 0;
  padding: 0 var(--sp-6);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.tab {
  padding: var(--sp-3) var(--sp-4);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color var(--t-fast), border-color var(--t-fast);
  margin-bottom: -1px;
}

.tab:hover    { color: var(--color-text-primary); }
.tab--active  { color: var(--color-accent); border-bottom-color: var(--color-accent); }

/* ── Tab content ─────────────────────────────────────────── */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-6);
}

/* ── Metrics ─────────────────────────────────────────────── */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}

.metric-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
  text-align: center;
}

.metric-card--accent {
  border-color: var(--color-accent);
  background: var(--color-accent-subtle);
}

.metric-value {
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text-primary);
  line-height: 1.2;
}

.metric-card--accent .metric-value {
  color: var(--color-accent);
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: var(--sp-1);
}

/* ── Confusion row ───────────────────────────────────────── */
.confusion-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
  margin-bottom: var(--sp-5);
}

.confusion-cell {
  padding: var(--sp-3);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  text-align: center;
}

.confusion-tp { background: var(--color-success-subtle); border-color: rgba(34, 197, 94, 0.2); }
.confusion-fp { background: var(--color-error-subtle);   border-color: rgba(239, 68, 68, 0.2); }
.confusion-fn { background: var(--color-warning-subtle); border-color: rgba(245, 158, 11, 0.2); }
.confusion-tn { background: var(--color-surface);        border-color: var(--color-border-subtle); }

.confusion-val {
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
}

.confusion-name {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* ── Summary ─────────────────────────────────────────────── */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-3);
}

.summary-item {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
}

.summary-val {
  font-size: var(--text-xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text-primary);
}

.val-error { color: var(--color-error); }

.summary-key {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--sp-1);
}

/* ── Loading ─────────────────────────────────────────────── */
.loading-state {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-8);
  color: var(--color-text-muted);
}
</style>
