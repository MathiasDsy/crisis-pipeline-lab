<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useBenchmarkStore } from '@/stores/benchmarkStore'
import AccordionSection     from '@/components/ui/AccordionSection.vue'
import MultiSelectDropdown  from '@/components/ui/MultiSelectDropdown.vue'
import type { SelectItem }  from '@/components/ui/MultiSelectDropdown.vue'
import BenchmarkProgress    from '@/components/benchmark/BenchmarkProgress.vue'
import BenchmarkLeaderboard from '@/components/benchmark/BenchmarkLeaderboard.vue'
import RunTweetClassification from '@/components/benchmark/RunTweetClassification.vue'
import RunMap               from '@/components/simulation/RunMap.vue'
import { downloadCsv }      from '@/utils/csv'

const store = useBenchmarkStore()

function modelName(key: string) {
  return store.classifiers.find((m) => m.model_key === key)?.name
    ?? store.extractors.find((m) => m.model_key === key)?.name
    ?? key
}

function exportLeaderboard() {
  const headers = [
    'rank', 'classifier', 'extractor', 'f1', 'precision', 'recall', 'accuracy',
    'tp', 'fp', 'fn', 'tn', 'total_tweets', 'status', 'run_id',
  ]
  const rows = store.leaderboard.map((e, i) => [
    i + 1,
    modelName(e.model_snapshot_json.classifier_model_key),
    modelName(e.model_snapshot_json.location_model_key),
    e.f1, e.precision, e.recall, e.accuracy,
    e.tp, e.fp, e.fn, e.tn, e.total_tweets, e.status, e.run_id,
  ])
  const name = store.benchmark?.name ?? 'benchmark'
  downloadCsv(`leaderboard-${name}`, headers, rows)
}

onMounted(() => {
  store.loadData()
  store.loadHistory()
})
onUnmounted(() => store.stopPolling())

function statusBadgeClass(status: string) {
  return status === 'completed' ? 'badge-success'
       : status === 'error'     ? 'badge-error'
       : status === 'cancelled' ? 'badge-cancelled'
       : 'badge-running'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

const canLaunch = computed(
  () =>
    !!store.selectedDatasetId &&
    store.selectedClassifiers.size > 0 &&
    store.selectedExtractors.size > 0 &&
    !store.isRunning,
)

const datasetItems = computed<SelectItem[]>(() =>
  store.datasets.map((d) => ({
    id:       d.id,
    label:    d.name,
    sublabel: d.metadata_json?.columns?.join(', ') as string | undefined,
    disabled: !d.is_valid,
  })),
)

const selectedDatasetSet = computed(() =>
  store.selectedDatasetId ? new Set([store.selectedDatasetId]) : new Set<string>(),
)

const classifierItems = computed<SelectItem[]>(() =>
  store.classifiers.map((m) => ({
    id: m.model_key, label: m.name, sublabel: m.model_key, disabled: !m.is_available,
  })),
)

const extractorItems = computed<SelectItem[]>(() =>
  store.extractors.map((m) => ({
    id: m.model_key, label: m.name, sublabel: m.model_key, disabled: !m.is_available,
  })),
)

const allModels = computed(() => [...store.classifiers, ...store.extractors])

const selectedRunName = computed(() => {
  const runId = store.selectedResultRunId
  if (!runId) return ''
  const entry = store.leaderboard.find((e) => e.run_id === runId)
  if (!entry) return runId.slice(0, 8)
  const c = store.classifiers.find((m) => m.model_key === entry.model_snapshot_json.classifier_model_key)
  const l = store.extractors.find((m) => m.model_key === entry.model_snapshot_json.location_model_key)
  return `${c?.name ?? entry.model_snapshot_json.classifier_model_key} + ${l?.name ?? entry.model_snapshot_json.location_model_key}`
})
</script>

<template>
  <div class="benchmark-page">

    <!-- ── Left: config ─────────────────────────────────── -->
    <aside class="config-panel">
      <div class="config-header">
        <h2 class="config-title">Benchmark</h2>
        <p class="text-xs text-muted">classifier × extractor matrix · runs server-side</p>
      </div>

      <div class="config-body">
        <!-- History éventail -->
        <AccordionSection
          title="Benchmarks"
          :badge="store.history.length ? String(store.history.length) : undefined"
          :initial-open="false"
        >
          <div class="history-body">
            <div v-if="store.isLoadingHistory" class="history-loading">
              <span class="spinner" />
              <span class="text-xs text-muted">Loading…</span>
            </div>

            <p v-else-if="store.history.length === 0" class="text-xs text-muted history-empty">
              No benchmarks yet.
            </p>

            <ul v-else class="history-list">
              <li
                v-for="bm in store.history"
                :key="bm.id"
                class="history-item"
                :class="{ 'history-item--active': store.benchmark?.id === bm.id }"
                @click="store.selectBenchmark(bm.id)"
              >
                <div class="history-item-top">
                  <span class="history-name truncate">{{ bm.name }}</span>
                  <span class="badge" :class="statusBadgeClass(bm.status)">
                    <span v-if="bm.status === 'running'" class="spinner" />
                    {{ bm.status }}
                  </span>
                </div>
                <div class="history-item-sub">
                  <span class="text-xs text-muted">{{ bm.completed_runs }}/{{ bm.total_runs }} runs</span>
                  <span class="text-xs text-muted">{{ formatDate(bm.created_at) }}</span>
                </div>
              </li>
            </ul>
          </div>
        </AccordionSection>

        <div class="divider" />

        <MultiSelectDropdown
          label="Dataset"
          single
          :items="datasetItems"
          :selected="selectedDatasetSet"
          :disabled="store.isRunning"
          @toggle="store.selectDataset"
        />

        <MultiSelectDropdown
          label="Relevance classifier"
          :items="classifierItems"
          :selected="store.selectedClassifiers"
          :disabled="store.isRunning"
          @toggle="store.toggleClassifier"
          @select-all="store.selectAllClassifiers"
        />

        <MultiSelectDropdown
          label="Location extractor"
          :items="extractorItems"
          :selected="store.selectedExtractors"
          :disabled="store.isRunning"
          @toggle="store.toggleExtractor"
          @select-all="store.selectAllExtractors"
        />

        <!-- Event matcher: fixed in V1 -->
        <div class="fixed-step">
          <div class="fixed-step-row">
            <span class="section-label">Event matcher · radius</span>
            <span class="badge badge-muted">{{ store.fixedRadiusKm }} km · fixed</span>
          </div>
          <p class="text-xs text-muted">
            Radius is fixed server-side in V1 — not part of the matrix.
          </p>
        </div>

        <!-- Launch -->
        <div class="launch-bar">
          <div class="combo-count">
            <span class="combo-num">{{ store.comboCount }}</span>
            <span class="text-xs text-muted">combo{{ store.comboCount !== 1 ? 's' : '' }}</span>
          </div>
          <button class="btn btn-primary" :disabled="!canLaunch" @click="store.launchBenchmark">
            <span v-if="store.isRunning" class="spinner" />
            {{ store.isRunning ? 'Running…' : 'Launch' }}
          </button>
        </div>

        <div v-if="store.error" class="text-sm" style="color:var(--color-error)">
          {{ store.error }}
        </div>
      </div>
    </aside>

    <!-- ── Right: results ───────────────────────────────── -->
    <main class="results-panel">
      <div v-if="store.isLoadingBoard && store.leaderboard.length === 0" class="board-loading">
        <span class="spinner" />
        <span class="text-sm text-muted">Loading leaderboard…</span>
      </div>

      <div v-else-if="!store.benchmark && store.leaderboard.length === 0" class="empty-state">
        <svg class="empty-state-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        <p class="text-sm">Select a past benchmark or launch a new one</p>
      </div>

      <template v-else>
        <BenchmarkProgress
          v-if="store.benchmark"
          :benchmark="store.benchmark"
          :completed-count="store.completedCount"
          :total-count="store.totalCount"
          :progress="store.progress"
          :is-running="store.isRunning"
          @cancel="store.cancelBenchmark"
        />

        <template v-if="store.leaderboard.length > 0">
          <div class="board-section">
            <div class="board-section-head">
              <span class="text-sm font-medium">Leaderboard</span>
              <button class="btn btn-outline btn-sm" @click="exportLeaderboard">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Export CSV
              </button>
            </div>
            <BenchmarkLeaderboard
              :entries="store.leaderboard"
              :selected-run-id="store.selectedResultRunId"
              :models="allModels"
              @select-run="store.selectResultForMap"
            />
          </div>

          <!-- Selected run: tweets + map -->
          <template v-if="store.selectedResultRunId">
            <RunTweetClassification
              :tweets="store.selectedRunTweets"
              :is-loading="store.isLoadingTweets"
            />

            <div class="map-section">
              <div class="map-section-header">
                <span class="text-sm font-medium">Events map</span>
                <span class="text-xs text-muted">
                  {{ selectedRunName ? `Run: ${selectedRunName}` : '' }}
                </span>
              </div>
              <div v-if="store.isLoadingEvents" class="map-loading">
                <span class="spinner" />
                <span class="text-sm text-muted">Loading events…</span>
              </div>
              <RunMap v-else :events="store.selectedResultEvents" />
            </div>
          </template>
        </template>
      </template>
    </main>

  </div>
</template>

<style scoped>
.benchmark-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* ── Config panel ────────────────────────────────────────── */
.config-panel {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.config-header {
  padding: var(--sp-4) var(--sp-4) var(--sp-3);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.config-title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
  margin-bottom: var(--sp-1);
}

.config-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-4) var(--sp-3);
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
}

/* ── History (éventail) ──────────────────────────────────── */
.history-body {
  padding-top: var(--sp-3);
}

.history-loading {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  color: var(--color-text-muted);
}

.history-empty { padding: var(--sp-1) 0; }

.history-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 260px;
  overflow-y: auto;
}

.history-item {
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--t-fast), border-color var(--t-fast);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.history-item:hover {
  background: var(--color-surface-elevated);
}

.history-item--active {
  background: var(--color-accent-subtle);
  border-color: rgba(59, 130, 246, 0.2);
}

.history-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.history-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  min-width: 0;
}

.history-item-sub {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

/* ── Board loading ───────────────────────────────────────── */
.board-loading {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-8);
  color: var(--color-text-muted);
}

/* ── Fixed step card ─────────────────────────────────────── */
.fixed-step {
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--sp-3) var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.fixed-step-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ── Launch bar ──────────────────────────────────────────── */
.launch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--sp-3);
  border-top: 1px solid var(--color-border-subtle);
}

.combo-count {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}

.combo-num {
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  line-height: 1;
}

/* ── Results panel ───────────────────────────────────────── */
.results-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-6);
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
}

.board-section {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.board-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.map-section {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.map-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.map-loading {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  height: 380px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-6);
  color: var(--color-text-muted);
}
</style>
