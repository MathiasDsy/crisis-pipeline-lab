import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { datasetService } from '@/services/datasetService'
import { pipelineService } from '@/services/pipelineService'
import { simulationService } from '@/services/simulationService'
import { runService } from '@/services/runService'
import type { Dataset } from '@/types/dataset'
import type { PipelineConfig } from '@/types/pipeline'
import type { Run, RunSummary, RunMetrics } from '@/types/run'
import type { FireEvent } from '@/types/event'
import type { Tweet, StepExecution } from '@/types/tweet'

export const useSimulationStore = defineStore('simulation', () => {
  // ── Core data ──────────────────────────────────────────
  const datasets  = ref<Dataset[]>([])
  const pipelines = ref<PipelineConfig[]>([])
  const runs      = ref<Run[]>([])

  // ── Selected run detail ────────────────────────────────
  const selectedRunId      = ref<string | null>(null)
  const selectedRunSummary = ref<RunSummary | null>(null)
  const selectedRunMetrics = ref<RunMetrics | null>(null)
  const selectedRunEvents  = ref<FireEvent[]>([])
  const selectedRunTweets  = ref<Tweet[]>([])
  const selectedRunTrace   = ref<StepExecution[]>([])

  // ── Loading / error states ─────────────────────────────
  const isLoadingDatasets  = ref(false)
  const isLoadingPipelines = ref(false)
  const isLoadingRuns      = ref(false)
  const isLoadingDetail    = ref(false)
  const isStarting         = ref(false)
  const error              = ref<string | null>(null)

  // ── Polling ────────────────────────────────────────────
  let pollTimer: ReturnType<typeof setInterval> | null = null

  // ── Computed ───────────────────────────────────────────
  const selectedRun = computed(() =>
    runs.value.find((r) => r.id === selectedRunId.value) ?? null,
  )

  const isPolling = computed(() => pollTimer !== null)

  // ── Actions ────────────────────────────────────────────
  async function loadDatasets() {
    isLoadingDatasets.value = true
    try {
      datasets.value = await datasetService.list()
    } catch {
      error.value = 'Impossible de charger les datasets'
    } finally {
      isLoadingDatasets.value = false
    }
  }

  async function loadPipelines() {
    isLoadingPipelines.value = true
    try {
      pipelines.value = await pipelineService.list()
    } catch {
      error.value = 'Impossible de charger les pipelines'
    } finally {
      isLoadingPipelines.value = false
    }
  }

  async function loadRuns() {
    isLoadingRuns.value = true
    try {
      runs.value = await runService.list()
    } catch {
      error.value = 'Impossible de charger les runs'
    } finally {
      isLoadingRuns.value = false
    }
  }

  async function startSimulation(datasetId: string, pipelineId: string, forceRerun = false) {
    isStarting.value = true
    error.value = null
    try {
      const res = await simulationService.start({
        dataset_id: datasetId,
        pipeline_config_id: pipelineId,
        force_rerun: forceRerun,
      })

      const existing = runs.value.findIndex((r) => r.id === res.run_id)
      if (existing === -1) {
        runs.value.unshift(res.run)
      } else {
        runs.value[existing] = res.run
      }

      await selectRun(res.run_id)

      if (res.run.status === 'running') {
        startPolling(res.run_id)
      }

      return res
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur lors du lancement'
      throw e
    } finally {
      isStarting.value = false
    }
  }

  async function cancelRun(runId: string) {
    try {
      await simulationService.cancel(runId)
      stopPolling()
      await refreshRun(runId)
    } catch {
      error.value = 'Impossible d\'annuler le run'
    }
  }

  async function selectRun(runId: string) {
    stopPolling()
    selectedRunId.value      = runId
    selectedRunSummary.value = null
    selectedRunMetrics.value = null
    selectedRunEvents.value  = []
    selectedRunTweets.value  = []
    selectedRunTrace.value   = []

    const run = runs.value.find((r) => r.id === runId)

    if (run?.status === 'running') {
      startPolling(runId)
      return
    }

    await loadRunDetail(runId)
  }

  async function loadRunDetail(runId: string) {
    isLoadingDetail.value = true
    try {
      const [summary, metrics, events, tweets, trace] = await Promise.allSettled([
        runService.summary(runId),
        runService.metrics(runId),
        runService.events(runId),
        runService.tweets(runId),
        runService.trace(runId),
      ])

      if (summary.status === 'fulfilled') selectedRunSummary.value = summary.value
      if (metrics.status === 'fulfilled') selectedRunMetrics.value = metrics.value
      if (events.status  === 'fulfilled') selectedRunEvents.value  = events.value
      if (tweets.status  === 'fulfilled') selectedRunTweets.value  = tweets.value
      if (trace.status   === 'fulfilled') selectedRunTrace.value   = trace.value
    } finally {
      isLoadingDetail.value = false
    }
  }

  async function refreshRun(runId: string): Promise<Run | null> {
    try {
      const run = await simulationService.getStatus(runId)
      const idx = runs.value.findIndex((r) => r.id === runId)
      if (idx !== -1) runs.value[idx] = run
      return run
    } catch {
      return null
    }
  }

  function startPolling(runId: string) {
    stopPolling()
    pollTimer = setInterval(async () => {
      const run = await refreshRun(runId)
      if (run && run.status !== 'running') {
        stopPolling()
        await loadRunDetail(runId)
      }
    }, 2500)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    datasets,
    pipelines,
    runs,
    selectedRunId,
    selectedRun,
    selectedRunSummary,
    selectedRunMetrics,
    selectedRunEvents,
    selectedRunTweets,
    selectedRunTrace,
    isLoadingDatasets,
    isLoadingPipelines,
    isLoadingRuns,
    isLoadingDetail,
    isStarting,
    isPolling,
    error,
    loadDatasets,
    loadPipelines,
    loadRuns,
    startSimulation,
    cancelRun,
    selectRun,
    stopPolling,
    clearError,
  }
})
