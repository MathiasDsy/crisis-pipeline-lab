<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePipelineStore } from '@/stores/pipelineStore'

const store = usePipelineStore()

const fileInput   = ref<HTMLInputElement | null>(null)
const isDragging  = ref(false)
const expandedId  = ref<string | null>(null)
const confirmId   = ref<string | null>(null)

onMounted(() => store.load())

function triggerFilePicker() {
  store.clearImportError()
  fileInput.value?.click()
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) await uploadFile(file)
  input.value = ''
}

async function uploadFile(file: File) {
  const ok = /\.(ya?ml)$/i.test(file.name)
  if (!ok) {
    store.importError = 'Seuls les fichiers .yaml / .yml sont acceptés'
    return
  }
  await store.importFile(file).catch(() => {})
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function askDelete(id: string) {
  confirmId.value = id
}

async function confirmDelete(id: string) {
  await store.remove(id)
  confirmId.value = null
}

interface Step {
  id?: string
  component_key?: string
  model_key?: string
}

function steps(config: Record<string, unknown>): Step[] {
  const s = config?.steps
  return Array.isArray(s) ? (s as Step[]) : []
}
</script>

<template>
  <div class="pipelines-page">
    <!-- Header -->
    <header class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Pipelines</h1>
        <div v-if="!store.isLoading" class="page-stats">
          <span class="stat-pill">{{ store.pipelines.length }} total</span>
          <span class="stat-pill stat-pill--ok">{{ store.validCount }} valid</span>
          <span v-if="store.invalidCount > 0" class="stat-pill stat-pill--err">
            {{ store.invalidCount }} invalid
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary btn-sm" :disabled="store.isImporting" @click="triggerFilePicker">
          <span v-if="store.isImporting" class="spinner" />
          {{ store.isImporting ? 'Importing…' : 'Import YAML' }}
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".yaml,.yml,text/yaml"
          class="hidden-input"
          @change="onFileSelected"
        />
      </div>
    </header>

    <!-- Errors -->
    <div v-if="store.error" class="error-banner text-sm">{{ store.error }}</div>
    <div v-if="store.importError" class="error-banner text-sm">
      Import failed — {{ store.importError }}
    </div>

    <!-- Body (drop zone) -->
    <div
      class="page-body"
      :class="{ 'page-body--dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragenter.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <div v-if="isDragging" class="drop-overlay">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <span class="text-sm">Drop a .yaml pipeline to import</span>
      </div>

      <!-- Loading -->
      <div v-if="store.isLoading" class="pipeline-list">
        <div v-for="n in 3" :key="n" class="pipeline-skeleton" />
      </div>

      <!-- Empty -->
      <div v-else-if="store.pipelines.length === 0" class="empty-state">
        <svg class="empty-state-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M4 5h16M4 12h16M4 19h16"/>
        </svg>
        <p class="text-sm">No pipelines yet.</p>
        <button class="btn btn-primary btn-sm" @click="triggerFilePicker">Import YAML</button>
      </div>

      <!-- List -->
      <ul v-else class="pipeline-list">
        <li
          v-for="pl in store.pipelines"
          :key="pl.id"
          class="pipeline-card"
          :class="{ 'pipeline-card--flash': pl.id === store.lastImportedId }"
        >
          <div class="pipeline-head">
            <span class="status-dot" :class="pl.is_valid ? 'status-dot--ok' : 'status-dot--err'" />

            <div class="pipeline-info">
              <div class="pipeline-name-row">
                <span class="pipeline-name">{{ pl.name }}</span>
                <span class="badge badge-muted">v{{ pl.version }}</span>
                <span class="badge" :class="pl.is_valid ? 'badge-success' : 'badge-error'">
                  {{ pl.is_valid ? 'valid' : 'invalid' }}
                </span>
              </div>
              <p v-if="pl.description" class="pipeline-desc text-sm text-secondary">
                {{ pl.description }}
              </p>
              <div class="pipeline-chips">
                <span
                  v-for="comp in pl.required_components_json"
                  :key="comp"
                  class="chip chip-component"
                >{{ comp }}</span>
                <span
                  v-for="model in pl.required_models_json"
                  :key="model"
                  class="chip chip-model font-mono"
                >{{ model }}</span>
              </div>
              <ul v-if="!pl.is_valid && pl.validation_errors.length" class="error-list">
                <li v-for="(err, i) in pl.validation_errors" :key="i" class="text-xs">{{ err }}</li>
              </ul>
            </div>

            <!-- Actions -->
            <div class="pipeline-actions">
              <button
                class="btn btn-outline btn-sm"
                :disabled="store.validatingIds.has(pl.id)"
                @click="store.validate(pl.id)"
              >
                <span v-if="store.validatingIds.has(pl.id)" class="spinner" />
                Validate
              </button>

              <!-- Delete with inline confirm -->
              <template v-if="confirmId === pl.id">
                <button
                  class="btn btn-danger btn-sm"
                  :disabled="store.deletingIds.has(pl.id)"
                  @click="confirmDelete(pl.id)"
                >
                  <span v-if="store.deletingIds.has(pl.id)" class="spinner" />
                  Confirm
                </button>
                <button class="btn btn-ghost btn-sm" @click="confirmId = null">Cancel</button>
              </template>
              <button v-else class="btn btn-ghost btn-sm delete-btn" @click="askDelete(pl.id)">
                Delete
              </button>

              <button class="btn btn-ghost btn-icon btn-sm" @click="toggleExpand(pl.id)">
                <svg
                  class="chevron"
                  :class="{ expanded: expandedId === pl.id }"
                  width="12" height="12" viewBox="0 0 12 12" fill="none"
                >
                  <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Expanded: steps -->
          <Transition name="slide-up">
            <div v-if="expandedId === pl.id" class="pipeline-steps">
              <div class="section-label steps-label">Steps</div>
              <div class="steps-flow">
                <template v-for="(step, i) in steps(pl.config_json)" :key="step.id ?? i">
                  <div class="step-node">
                    <span class="step-node-name">{{ step.id ?? step.component_key }}</span>
                    <span class="step-node-comp text-xs text-muted">{{ step.component_key }}</span>
                    <span v-if="step.model_key" class="step-node-model font-mono text-xs">
                      {{ step.model_key }}
                    </span>
                  </div>
                  <svg
                    v-if="i < steps(pl.config_json).length - 1"
                    class="step-arrow"
                    width="16" height="16" viewBox="0 0 16 16" fill="none"
                  >
                    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </template>
              </div>
              <div class="steps-meta text-xs text-muted">
                Source: {{ pl.original_filename }}
              </div>
            </div>
          </Transition>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.pipelines-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header (shared style with datasets) ─────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.page-header-left { display: flex; align-items: center; gap: var(--sp-4); }
.page-title { font-size: var(--text-xl); font-weight: var(--fw-semibold); }
.page-stats { display: flex; gap: var(--sp-2); }

.stat-pill {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
}
.stat-pill--ok  { color: var(--color-success); background: var(--color-success-subtle); }
.stat-pill--err { color: var(--color-error);   background: var(--color-error-subtle); }

.header-actions { display: flex; align-items: center; gap: var(--sp-2); }
.hidden-input { display: none; }

/* ── Error ───────────────────────────────────────────────── */
.error-banner {
  padding: var(--sp-3) var(--sp-6);
  background: var(--color-error-subtle);
  color: var(--color-error);
  flex-shrink: 0;
}

/* ── Body / drop zone ────────────────────────────────────── */
.page-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-5) var(--sp-6);
  position: relative;
}

.page-body--dragging {
  outline: 2px dashed var(--color-accent);
  outline-offset: -8px;
  border-radius: var(--radius-lg);
}

.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  background: rgba(2, 6, 23, 0.85);
  color: var(--color-accent);
  pointer-events: none;
}

/* ── List ────────────────────────────────────────────────── */
.pipeline-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  max-width: 960px;
  margin: 0 auto;
}

.pipeline-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--t-fast);
}

.pipeline-card:hover { border-color: var(--color-border); }

.pipeline-card--flash { animation: flash-in 1.6s ease; }

@keyframes flash-in {
  0%   { border-color: var(--color-accent); background: var(--color-accent-subtle); }
  100% { border-color: var(--color-border-subtle); background: var(--color-surface); }
}

.pipeline-head {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-4);
}

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}
.status-dot--ok  { background: var(--color-success); }
.status-dot--err { background: var(--color-error); }

.pipeline-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.pipeline-name-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.pipeline-name { font-size: var(--text-md); font-weight: var(--fw-medium); }
.pipeline-desc { margin: 0; }

.pipeline-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
}

.chip {
  font-size: var(--text-xs);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
}
.chip-component { background: var(--color-accent-subtle); color: var(--color-accent); }
.chip-model     { background: var(--color-surface-elevated); color: var(--color-text-secondary); }

.error-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: var(--color-error);
  padding: var(--sp-2);
  background: var(--color-error-subtle);
  border-radius: var(--radius-sm);
}

/* ── Actions ─────────────────────────────────────────────── */
.pipeline-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-shrink: 0;
}

.delete-btn:hover { color: var(--color-error); }

.chevron { color: var(--color-text-muted); transition: transform var(--t-fast); }
.chevron.expanded { transform: rotate(180deg); }

/* ── Steps ───────────────────────────────────────────────── */
.pipeline-steps {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--sp-4);
  background: var(--color-bg);
}

.steps-label { margin-bottom: var(--sp-3); }

.steps-flow {
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.step-node {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--color-surface-elevated);
  border-radius: var(--radius-md);
  min-width: 130px;
}

.step-node-name { font-size: var(--text-sm); font-weight: var(--fw-medium); }
.step-node-model { color: var(--color-accent); }

.step-arrow {
  align-self: center;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.steps-meta { margin-top: var(--sp-3); }

/* ── Skeleton ────────────────────────────────────────────── */
.pipeline-skeleton {
  height: 96px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50%      { opacity: 0.4; }
}
</style>
