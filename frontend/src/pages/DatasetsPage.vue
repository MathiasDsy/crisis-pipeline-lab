<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDatasetStore } from '@/stores/datasetStore'

const store = useDatasetStore()

const API_URL = (import.meta.env.VITE_API_URL as string) ?? 'http://localhost:8000'

const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

onMounted(() => store.load())

function downloadUrl(id: string) {
  return `${API_URL}/datasets/${id}/download`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function triggerFilePicker() {
  store.clearImportError()
  fileInput.value?.click()
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) await uploadFile(file)
  input.value = '' // reset so selecting the same file again re-fires
}

async function uploadFile(file: File) {
  if (!file.name.toLowerCase().endsWith('.csv')) {
    store.importError = 'Seuls les fichiers .csv sont acceptés'
    return
  }
  await store.importCsv(file).catch(() => {})
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}
</script>

<template>
  <div class="datasets-page">
    <!-- Header -->
    <header class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Datasets</h1>
        <div v-if="!store.isLoading" class="page-stats">
          <span class="stat-pill">{{ store.datasets.length }} total</span>
          <span class="stat-pill stat-pill--ok">{{ store.validCount }} valid</span>
          <span v-if="store.invalidCount > 0" class="stat-pill stat-pill--err">
            {{ store.invalidCount }} invalid
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button
          class="btn btn-outline btn-sm"
          :disabled="store.isDiscovering"
          @click="store.discover"
        >
          <span v-if="store.isDiscovering" class="spinner" />
          {{ store.isDiscovering ? 'Scanning…' : 'Rescan storage' }}
        </button>
        <button
          class="btn btn-primary btn-sm"
          :disabled="store.isImporting"
          @click="triggerFilePicker"
        >
          <span v-if="store.isImporting" class="spinner" />
          {{ store.isImporting ? 'Importing…' : 'Import CSV' }}
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".csv,text/csv"
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

    <!-- Body (also a drop zone) -->
    <div
      class="page-body"
      :class="{ 'page-body--dragging': isDragging }"
      @dragover.prevent="isDragging = true"
      @dragenter.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <!-- Drag overlay -->
      <div v-if="isDragging" class="drop-overlay">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <span class="text-sm">Drop a .csv file to import</span>
      </div>

      <!-- Loading -->
      <div v-if="store.isLoading" class="dataset-list">
        <div v-for="n in 4" :key="n" class="dataset-skeleton" />
      </div>

      <!-- Empty -->
      <div v-else-if="store.datasets.length === 0" class="empty-state">
        <svg class="empty-state-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
          <path d="M3 12a9 3 0 0 0 18 0"/>
        </svg>
        <p class="text-sm">No datasets found.</p>
        <div class="empty-actions">
          <button class="btn btn-primary btn-sm" @click="triggerFilePicker">Import CSV</button>
          <button class="btn btn-outline btn-sm" @click="store.discover">Rescan storage</button>
        </div>
      </div>

      <!-- List -->
      <ul v-else class="dataset-list">
        <li
          v-for="ds in store.datasets"
          :key="ds.id"
          class="dataset-card"
          :class="{ 'dataset-card--flash': ds.id === store.lastImportedId }"
        >
          <div class="dataset-main" @click="store.openPreview(ds.id)">
            <!-- Status dot -->
            <span class="status-dot" :class="ds.is_valid ? 'status-dot--ok' : 'status-dot--err'" />

            <!-- Info -->
            <div class="dataset-info">
              <div class="dataset-name-row">
                <span class="dataset-name">{{ ds.name }}</span>
                <span class="badge" :class="ds.is_valid ? 'badge-success' : 'badge-error'">
                  {{ ds.is_valid ? 'valid' : 'invalid' }}
                </span>
              </div>
              <div class="dataset-meta">
                <span class="font-mono text-xs text-muted truncate">{{ ds.path }}</span>
              </div>
              <div class="dataset-columns">
                <span
                  v-for="col in ds.metadata_json?.columns ?? []"
                  :key="col"
                  class="col-chip"
                >
                  {{ col }}
                </span>
              </div>
              <!-- Validation errors -->
              <ul v-if="!ds.is_valid && ds.validation_errors.length" class="error-list">
                <li v-for="(err, i) in ds.validation_errors" :key="i" class="text-xs">
                  {{ err }}
                </li>
              </ul>
            </div>

            <!-- Right meta -->
            <div class="dataset-side">
              <a
                class="btn btn-ghost btn-icon btn-sm download-btn"
                :href="downloadUrl(ds.id)"
                :download="ds.metadata_json?.filename ?? `${ds.name}.csv`"
                title="Download CSV"
                @click.stop
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </a>
              <span class="text-xs text-muted">{{ formatDate(ds.updated_at) }}</span>
              <svg
                class="chevron"
                :class="{ expanded: store.previewId === ds.id }"
                width="12" height="12" viewBox="0 0 12 12" fill="none"
              >
                <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
            </div>
          </div>

          <!-- Preview panel -->
          <Transition name="slide-up">
            <div v-if="store.previewId === ds.id" class="dataset-preview">
              <div v-if="store.isLoadingPreview" class="preview-loading">
                <span class="spinner" />
                <span class="text-sm text-muted">Loading preview…</span>
              </div>
              <div v-else-if="store.preview" class="preview-table-wrap">
                <table class="preview-table">
                  <thead>
                    <tr>
                      <th v-for="col in store.preview.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in store.preview.rows" :key="i">
                      <td v-for="col in store.preview.columns" :key="col" class="truncate">
                        {{ row[col] }}
                      </td>
                    </tr>
                  </tbody>
                </table>
                <span class="text-xs text-muted preview-count">
                  First {{ store.preview.count }} rows
                </span>
              </div>
            </div>
          </Transition>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.datasets-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Header ──────────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--fw-semibold);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.hidden-input {
  display: none;
}

.page-stats {
  display: flex;
  gap: var(--sp-2);
}

.stat-pill {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
}

.stat-pill--ok  { color: var(--color-success); background: var(--color-success-subtle); }
.stat-pill--err { color: var(--color-error);   background: var(--color-error-subtle); }

/* ── Error ───────────────────────────────────────────────── */
.error-banner {
  padding: var(--sp-3) var(--sp-6);
  background: var(--color-error-subtle);
  color: var(--color-error);
  flex-shrink: 0;
}

/* ── Body ────────────────────────────────────────────────── */
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

.empty-actions {
  display: flex;
  gap: var(--sp-2);
}

.dataset-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  max-width: 900px;
  margin: 0 auto;
}

/* ── Card ────────────────────────────────────────────────── */
.dataset-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color var(--t-fast);
}

.dataset-card:hover {
  border-color: var(--color-border);
}

.dataset-card--flash {
  animation: flash-in 1.6s ease;
}

@keyframes flash-in {
  0%   { border-color: var(--color-accent); background: var(--color-accent-subtle); }
  100% { border-color: var(--color-border-subtle); background: var(--color-surface); }
}

.dataset-main {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-4);
  cursor: pointer;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.status-dot--ok  { background: var(--color-success); }
.status-dot--err { background: var(--color-error); }

.dataset-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.dataset-name-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.dataset-name {
  font-size: var(--text-md);
  font-weight: var(--fw-medium);
}

.dataset-meta { min-width: 0; }

.dataset-columns {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
}

.col-chip {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
}

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

.dataset-side {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-shrink: 0;
}

.download-btn {
  color: var(--color-text-muted);
}

.download-btn:hover {
  color: var(--color-accent);
}

.chevron {
  color: var(--color-text-muted);
  transition: transform var(--t-fast);
}

.chevron.expanded { transform: rotate(180deg); }

/* ── Preview ─────────────────────────────────────────────── */
.dataset-preview {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--sp-4);
  background: var(--color-bg);
}

.preview-loading {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  color: var(--color-text-muted);
}

.preview-table-wrap {
  overflow-x: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.preview-table th {
  text-align: left;
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border-subtle);
  white-space: nowrap;
}

.preview-table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  max-width: 320px;
}

.preview-table tbody tr:last-child td { border-bottom: none; }

.preview-count {
  display: block;
  margin-top: var(--sp-2);
}

/* ── Skeleton ────────────────────────────────────────────── */
.dataset-skeleton {
  height: 88px;
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
