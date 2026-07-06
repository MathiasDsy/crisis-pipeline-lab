import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { datasetService }   from '@/services/datasetService'
import { modelService }     from '@/services/modelService'
import { benchmarkService } from '@/services/benchmarkService'
import { runService }       from '@/services/runService'
import type { Dataset }     from '@/types/dataset'
import type { Model }       from '@/types/model'
import type { FireEvent }   from '@/types/event'
import type { ClassifiedTweet, ClassKind } from '@/types/tweet'
import type { Benchmark, LeaderboardEntry } from '@/types/benchmark'

// Radius is fixed server-side in V1 (event_matcher structure is static).
const FIXED_RADIUS_KM = 5

export const useBenchmarkStore = defineStore('benchmark', () => {
  // ── Reference data ─────────────────────────────────────
  const datasets    = ref<Dataset[]>([])
  const classifiers = ref<Model[]>([])
  const extractors  = ref<Model[]>([])

  // ── User selections ─────────────────────────────────────
  const selectedDatasetId   = ref<string>('')
  const selectedClassifiers = ref<Set<string>>(new Set())
  const selectedExtractors  = ref<Set<string>>(new Set())

  // ── Benchmark run state ─────────────────────────────────
  const benchmark   = ref<Benchmark | null>(null)
  const leaderboard = ref<LeaderboardEntry[]>([])
  const isRunning   = ref(false)

  // ── History ─────────────────────────────────────────────
  const history          = ref<Benchmark[]>([])
  const isLoadingHistory = ref(false)
  const isLoadingBoard   = ref(false)

  // ── Selected result for map ─────────────────────────────
  const selectedResultRunId  = ref<string | null>(null)
  const selectedResultEvents = ref<FireEvent[]>([])
  const isLoadingEvents      = ref(false)

  // ── Selected result: classified tweets ──────────────────
  const selectedRunTweets = ref<ClassifiedTweet[]>([])
  const isLoadingTweets   = ref(false)

  // ── Loading / error ─────────────────────────────────────
  const isLoadingData = ref(false)
  const error         = ref<string | null>(null)

  // ── Polling ─────────────────────────────────────────────
  let pollTimer: ReturnType<typeof setInterval> | null = null

  // ── Computed ────────────────────────────────────────────
  const comboCount = computed(
    () => selectedClassifiers.value.size * selectedExtractors.value.size,
  )

  const completedCount = computed(() => benchmark.value?.completed_runs ?? 0)
  const totalCount     = computed(() => benchmark.value?.total_runs ?? comboCount.value)

  const progress = computed(() =>
    totalCount.value === 0 ? 0 : (completedCount.value / totalCount.value) * 100,
  )

  const fixedRadiusKm = FIXED_RADIUS_KM

  // ── Actions ─────────────────────────────────────────────
  async function loadData() {
    isLoadingData.value = true
    error.value = null
    try {
      const [ds, models] = await Promise.all([
        datasetService.list(),
        modelService.list({ available: true }),
      ])
      datasets.value    = ds
      classifiers.value = models.filter((m) =>
        m.compatible_components_key.includes('relevance_classifier'),
      )
      extractors.value  = models.filter((m) =>
        m.compatible_components_key.includes('location_extractor'),
      )
    } catch {
      error.value = 'Impossible de charger les données'
    } finally {
      isLoadingData.value = false
    }
  }

  async function loadHistory() {
    isLoadingHistory.value = true
    try {
      history.value = await benchmarkService.list()
    } catch {
      // silent — history is non-critical
    } finally {
      isLoadingHistory.value = false
    }
  }

  // Load a past (or another) benchmark into the results panel.
  async function selectBenchmark(id: string) {
    stopPolling()
    isLoadingBoard.value = true
    selectedResultRunId.value  = null
    selectedResultEvents.value = []
    try {
      const [bm, board] = await Promise.all([
        benchmarkService.get(id),
        benchmarkService.leaderboard(id),
      ])
      benchmark.value   = bm
      leaderboard.value = board.leaderboard
      isRunning.value   = bm.status === 'running'

      if (board.leaderboard.length > 0) {
        await selectResultForMap(board.leaderboard[0]!.run_id)
      }
      if (bm.status === 'running') startPolling(id)
    } catch {
      error.value = 'Impossible de charger ce benchmark'
    } finally {
      isLoadingBoard.value = false
    }
  }

  function selectDataset(id: string) {
    // Single-select semantics: clicking the current one clears it.
    selectedDatasetId.value = selectedDatasetId.value === id ? '' : id
  }

  function toggleClassifier(key: string) {
    if (selectedClassifiers.value.has(key)) selectedClassifiers.value.delete(key)
    else selectedClassifiers.value.add(key)
  }

  function toggleExtractor(key: string) {
    if (selectedExtractors.value.has(key)) selectedExtractors.value.delete(key)
    else selectedExtractors.value.add(key)
  }

  function selectAllClassifiers() {
    const keys = classifiers.value.filter((m) => m.is_available).map((m) => m.model_key)
    const allSelected = keys.every((k) => selectedClassifiers.value.has(k))
    selectedClassifiers.value = allSelected ? new Set() : new Set(keys)
  }

  function selectAllExtractors() {
    const keys = extractors.value.filter((m) => m.is_available).map((m) => m.model_key)
    const allSelected = keys.every((k) => selectedExtractors.value.has(k))
    selectedExtractors.value = allSelected ? new Set() : new Set(keys)
  }

  async function launchBenchmark() {
    if (!selectedDatasetId.value || comboCount.value === 0 || isRunning.value) return

    isRunning.value    = true
    error.value        = null
    leaderboard.value  = []
    benchmark.value    = null
    selectedResultRunId.value  = null
    selectedResultEvents.value = []

    const dsName = datasets.value.find((d) => d.id === selectedDatasetId.value)?.name ?? 'benchmark'

    try {
      const res = await benchmarkService.start({
        dataset_id:            selectedDatasetId.value,
        classifier_model_keys: [...selectedClassifiers.value],
        location_model_keys:   [...selectedExtractors.value],
        name:                  `Benchmark ${dsName} — ${new Date().toLocaleString('en-GB')}`,
      })
      benchmark.value = res.benchmark
      history.value.unshift(res.benchmark)
      startPolling(res.benchmark_id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur au lancement du benchmark'
      isRunning.value = false
    }
  }

  async function cancelBenchmark() {
    if (!benchmark.value) return
    try {
      await benchmarkService.cancel(benchmark.value.id)
    } catch {
      // ignore — the poll loop will reflect the final state
    }
  }

  function startPolling(benchmarkId: string) {
    stopPolling()
    pollTimer = setInterval(() => refreshBenchmark(benchmarkId), 2500)
    // Kick off an immediate refresh so results stream in fast.
    refreshBenchmark(benchmarkId)
  }

  async function refreshBenchmark(benchmarkId: string) {
    try {
      const [bm, lb] = await Promise.all([
        benchmarkService.get(benchmarkId),
        benchmarkService.leaderboard(benchmarkId),
      ])
      benchmark.value   = bm
      leaderboard.value = lb.leaderboard

      // Keep the history entry's progress in sync.
      const hi = history.value.findIndex((b) => b.id === bm.id)
      if (hi !== -1) history.value[hi] = bm

      // Auto-select the current best run for the map.
      if (!selectedResultRunId.value && lb.leaderboard.length > 0) {
        await selectResultForMap(lb.leaderboard[0]!.run_id)
      }

      if (bm.status !== 'running') {
        stopPolling()
        isRunning.value = false
      }
    } catch {
      // transient error — keep polling
    }
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  async function selectResultForMap(runId: string) {
    selectedResultRunId.value  = runId
    selectedResultEvents.value = []
    selectedRunTweets.value    = []
    isLoadingEvents.value      = true
    isLoadingTweets.value      = true

    // Events (map)
    runService
      .events(runId)
      .then((ev) => { selectedResultEvents.value = ev })
      .catch(() => {})
      .finally(() => { isLoadingEvents.value = false })

    // Tweets from /runs/{run_id}/tweets, enriched with TP/FP/FN/TN from metrics.per_tweet.
    Promise.all([
      runService.tweets(runId, 1000),
      runService.metrics(runId).catch(() => null),
    ])
      .then(([tweets, metrics]) => {
        const classById = new Map(
          (metrics?.per_tweet ?? []).map((p) => [p.tweet_id, p]),
        )
        selectedRunTweets.value = tweets.map((t) => {
          const c = classById.get(t.id)
          const label     = c?.label ?? t.label ?? null
          const predicted = c?.predicted ?? null
          return {
            tweet_id:  t.id,
            text:      t.content,
            label,
            predicted,
            kind:      label !== null && predicted !== null ? classify(label, predicted) : null,
          }
        })
      })
      .catch(() => {})
      .finally(() => { isLoadingTweets.value = false })
  }

  function reset() {
    stopPolling()
    benchmark.value            = null
    leaderboard.value          = []
    isRunning.value            = false
    selectedResultRunId.value  = null
    selectedResultEvents.value = []
    error.value                = null
  }

  return {
    datasets,
    classifiers,
    extractors,
    selectedDatasetId,
    selectedClassifiers,
    selectedExtractors,
    fixedRadiusKm,
    benchmark,
    leaderboard,
    isRunning,
    history,
    isLoadingHistory,
    isLoadingBoard,
    selectedResultRunId,
    selectedResultEvents,
    isLoadingEvents,
    selectedRunTweets,
    isLoadingTweets,
    isLoadingData,
    error,
    comboCount,
    completedCount,
    totalCount,
    progress,
    loadData,
    loadHistory,
    selectBenchmark,
    selectDataset,
    toggleClassifier,
    toggleExtractor,
    selectAllClassifiers,
    selectAllExtractors,
    launchBenchmark,
    cancelBenchmark,
    selectResultForMap,
    stopPolling,
    reset,
  }
})

function classify(label: boolean, predicted: boolean): ClassKind {
  if (label && predicted) return 'TP'
  if (!label && predicted) return 'FP'
  if (label && !predicted) return 'FN'
  return 'TN'
}
