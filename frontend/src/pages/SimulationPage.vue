<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useSimulationStore } from '@/stores/simulationStore'
import RunListPanel from '@/components/simulation/RunListPanel.vue'
import NewRunForm   from '@/components/simulation/NewRunForm.vue'
import RunDetail    from '@/components/simulation/RunDetail.vue'

const store      = useSimulationStore()
const showNewRun = ref(false)

onMounted(async () => {
  await Promise.all([
    store.loadDatasets(),
    store.loadPipelines(),
    store.loadRuns(),
  ])
})

onUnmounted(() => {
  store.stopPolling()
})

async function handleSubmit(payload: {
  datasetId:  string
  pipelineId: string
  forceRerun: boolean
}) {
  await store.startSimulation(payload.datasetId, payload.pipelineId, payload.forceRerun)
  showNewRun.value = false
}

function handleSelectRun(runId: string) {
  store.selectRun(runId)
}
</script>

<template>
  <div class="simulation-page">
    <!-- Run list panel (left) -->
    <RunListPanel
      :runs="store.runs"
      :datasets="store.datasets"
      :pipelines="store.pipelines"
      :selected-run-id="store.selectedRunId"
      :is-loading="store.isLoadingRuns"
      @select="handleSelectRun"
      @new-run="showNewRun = true"
    />

    <!-- Main area (right) -->
    <div class="main-area">
      <!-- Error banner -->
      <Transition name="slide-up">
        <div v-if="store.error" class="error-banner">
          <span class="text-sm">{{ store.error }}</span>
          <button class="btn btn-ghost btn-sm btn-icon" @click="store.clearError">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </Transition>

      <!-- New run form -->
      <Transition name="slide-up">
        <div v-if="showNewRun" class="new-run-wrapper">
          <NewRunForm
            :datasets="store.datasets"
            :pipelines="store.pipelines"
            :is-starting="store.isStarting"
            @submit="handleSubmit"
            @cancel="showNewRun = false"
          />
        </div>
      </Transition>

      <!-- Run detail -->
      <RunDetail
        v-if="store.selectedRun && !showNewRun"
        :run="store.selectedRun"
        :summary="store.selectedRunSummary"
        :metrics="store.selectedRunMetrics"
        :events="store.selectedRunEvents"
        :tweets="store.selectedRunTweets"
        :trace="store.selectedRunTrace"
        :is-loading="store.isLoadingDetail"
        :is-polling="store.isPolling"
        @cancel="store.cancelRun($event)"
      />

      <!-- Empty state -->
      <div
        v-else-if="!showNewRun && !store.selectedRun"
        class="empty-state"
      >
        <svg class="empty-state-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        <p class="text-sm">Select a run or start a new simulation</p>
        <button class="btn btn-primary btn-sm" @click="showNewRun = true">New run</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.simulation-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.main-area {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--color-error-subtle);
  border-bottom: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--color-error);
  flex-shrink: 0;
}

.new-run-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-6);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  max-width: 560px;
}
</style>
