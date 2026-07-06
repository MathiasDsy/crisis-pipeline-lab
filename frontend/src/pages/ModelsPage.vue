<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useModelStore } from '@/stores/modelStore'
import type { ModelTab } from '@/stores/modelStore'
import type { HfModel } from '@/types/huggingface'

const store = useModelStore()

const zipInput = ref<HTMLInputElement | null>(null)
const showZipHelp = ref(false)

onMounted(() => store.loadInstalled())

function triggerZipPicker() {
  store.clearZipError()
  zipInput.value?.click()
}

async function onZipSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      store.zipError = 'Seuls les fichiers .zip sont acceptés'
    } else {
      await store.importZip(file)
    }
  }
  input.value = ''
}

const metadataExample = `{
  "model_key": "my_model_v1",
  "name": "My Model",
  "model_type": "classifier",
  "version": "1.0.0",
  "entrypoint": ".",
  "loader": "transformers",
  "compatible_components": ["relevance_classifier"]
}`

const tabs: { key: ModelTab; label: string }[] = [
  { key: 'classifier', label: 'Classifiers' },
  { key: 'ner',        label: 'NER / Location' },
]

function fmtNum(n: number | null) {
  if (n === null || n === undefined) return '—'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

function onEnter(e: KeyboardEvent) {
  if (e.key === 'Enter') store.search()
}

function importResult(hf: HfModel) {
  store.importModel(hf)
}
</script>

<template>
  <div class="models-page">

    <!-- ── Left: installed models ───────────────────────── -->
    <aside class="installed-panel">
      <div class="panel-header">
        <h2 class="panel-title">Installed</h2>
        <button
          class="btn btn-ghost btn-sm"
          :disabled="store.isDiscovering"
          @click="store.discover"
        >
          <span v-if="store.isDiscovering" class="spinner" />
          Rescan
        </button>
      </div>

      <!-- Section tabs -->
      <div class="installed-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="installed-tab"
          :class="{ 'installed-tab--active': store.activeTab === tab.key }"
          @click="store.setTab(tab.key)"
        >
          {{ tab.label }}
          <span class="installed-tab-count">
            {{ store.installed.filter((m) => m.compatible_components_key.includes(tab.key === 'classifier' ? 'relevance_classifier' : 'location_extractor')).length }}
          </span>
        </button>
      </div>

      <!-- Import own model -->
      <div class="import-zip-bar">
        <button
          class="btn btn-outline btn-sm import-zip-btn"
          :disabled="store.isUploadingZip"
          @click="triggerZipPicker"
        >
          <span v-if="store.isUploadingZip" class="spinner" />
          <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {{ store.isUploadingZip ? 'Uploading…' : 'Import .zip' }}
        </button>
        <button class="btn btn-ghost btn-icon btn-sm" title="Expected format" @click="showZipHelp = !showZipHelp">
          <span style="font-weight:600">?</span>
        </button>
        <input ref="zipInput" type="file" accept=".zip" class="hidden-input" @change="onZipSelected" />
      </div>

      <Transition name="slide-up">
        <div v-if="showZipHelp" class="zip-help">
          <p class="text-xs text-secondary">The .zip must contain a <code>metadata.json</code> at its root:</p>
          <pre class="zip-help-code font-mono">{{ metadataExample }}</pre>
        </div>
      </Transition>

      <div v-if="store.zipError" class="zip-error text-xs">{{ store.zipError }}</div>

      <div class="panel-body">
        <div v-if="store.isLoading" class="installed-loading">
          <span class="spinner" />
        </div>

        <div v-else-if="store.installedByTab.length === 0" class="empty-state">
          <p class="text-sm text-muted">
            No {{ store.activeTab === 'classifier' ? 'classifier' : 'NER' }} models installed.
          </p>
        </div>

        <ul v-else class="installed-list">
          <li v-for="m in store.installedByTab" :key="m.id" class="installed-item">
            <span
              class="avail-dot"
              :class="m.is_available ? 'avail-dot--ok' : 'avail-dot--off'"
              :title="m.is_available ? 'available' : 'missing on disk'"
            />
            <div class="installed-info">
              <span class="installed-name truncate">{{ m.name }}</span>
              <span class="installed-key font-mono text-xs text-muted truncate">{{ m.model_key }}</span>
              <div class="installed-tags">
                <span
                  v-for="c in m.compatible_components_key"
                  :key="c"
                  class="mini-chip"
                >{{ c }}</span>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </aside>

    <!-- ── Right: HuggingFace browser ───────────────────── -->
    <main class="browser-panel">
      <div class="browser-header">
        <div class="browser-title-row">
          <h1 class="browser-title">HuggingFace browser</h1>
          <a class="text-xs" href="https://huggingface.co/models" target="_blank" rel="noopener">
            huggingface.co ↗
          </a>
        </div>

        <!-- Tabs -->
        <div class="browser-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="browser-tab"
            :class="{ 'browser-tab--active': store.activeTab === tab.key }"
            @click="store.setTab(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Search bar -->
        <div class="search-row">
          <div class="search-input-wrap">
            <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              v-model="store.query"
              class="form-input search-input"
              :placeholder="store.activeTab === 'classifier' ? 'Search text-classification models…' : 'Search NER / token-classification models…'"
              @keydown="onEnter"
            />
          </div>
          <button class="btn btn-primary" :disabled="store.isSearching || !store.query.trim()" @click="store.search">
            <span v-if="store.isSearching" class="spinner" />
            Search
          </button>
        </div>

        <!-- Param budget slider -->
        <div class="param-filter">
          <div class="param-filter-head">
            <span class="text-xs text-secondary">Max parameters</span>
            <span class="param-value">
              {{ store.paramLimitReached ? 'No limit' : `≤ ${store.maxParamsM} M` }}
            </span>
          </div>
          <input
            v-model.number="store.maxParamsM"
            type="range"
            class="param-slider"
            min="10"
            :max="store.MAX_PARAMS_M"
            step="10"
          />
        </div>

        <div v-if="store.importError" class="import-error text-sm">
          Import failed — {{ store.importError }}
        </div>
      </div>

      <!-- Results -->
      <div class="browser-body">
        <div v-if="store.searchError" class="text-sm" style="color:var(--color-error)">
          {{ store.searchError }}
        </div>

        <div v-else-if="store.isSearching" class="results-loading">
          <span class="spinner" />
          <span class="text-sm text-muted">Searching HuggingFace…</span>
        </div>

        <div v-else-if="!store.hasSearched" class="empty-state">
          <svg class="empty-state-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p class="text-sm">Search HuggingFace for {{ store.activeTab === 'classifier' ? 'classifier' : 'NER' }} models to download.</p>
        </div>

        <div v-else-if="store.results.length === 0" class="empty-state">
          <p class="text-sm text-muted">No results for “{{ store.query }}”.</p>
        </div>

        <div v-else-if="store.filteredResults.length === 0" class="empty-state">
          <p class="text-sm text-muted">
            {{ store.results.length }} result(s) hidden by the {{ store.maxParamsM }} M param filter.
          </p>
        </div>

        <ul v-else class="results-list">
          <li
            v-if="store.filteredResults.length < store.results.length"
            class="results-hint text-xs text-muted"
          >
            Showing {{ store.filteredResults.length }} of {{ store.results.length }} (filtered by ≤ {{ store.maxParamsM }} M params)
          </li>
          <li v-for="hf in store.filteredResults" :key="hf.repo_id" class="result-card">
            <div class="result-main">
              <div class="result-top">
                <a class="result-name" :href="hf.url" target="_blank" rel="noopener">{{ hf.repo_id }}</a>
                <span v-if="hf.pipeline_tag" class="badge badge-muted">{{ hf.pipeline_tag }}</span>
              </div>

              <div class="result-stats">
                <span class="result-stat" title="parameters">
                  <strong>{{ hf.size_label ?? '—' }}</strong> params
                </span>
                <span class="result-stat" title="downloads">↓ {{ fmtNum(hf.downloads) }}</span>
                <span class="result-stat" title="likes">♥ {{ fmtNum(hf.likes) }}</span>
                <span v-if="hf.size_on_disk_mb" class="result-stat">{{ hf.size_on_disk_mb }} MB</span>
              </div>

              <div v-if="hf.tags?.length" class="result-tags">
                <span v-for="t in hf.tags.slice(0, 5)" :key="t" class="mini-chip">{{ t }}</span>
              </div>
            </div>

            <!-- Action -->
            <div class="result-action">
              <span v-if="store.isInstalled(hf)" class="badge badge-success">installed</span>
              <button
                v-else
                class="btn btn-outline btn-sm"
                :disabled="store.importingRepos.has(hf.repo_id)"
                @click="importResult(hf)"
              >
                <span v-if="store.importingRepos.has(hf.repo_id)" class="spinner" />
                <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                {{ store.importingRepos.has(hf.repo_id) ? 'Downloading…' : 'Download' }}
              </button>
            </div>
          </li>
        </ul>
      </div>
    </main>

  </div>
</template>

<style scoped>
.models-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* ── Installed panel (left) ──────────────────────────────── */
.installed-panel {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-4) var(--sp-4) var(--sp-3);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.panel-title { font-size: var(--text-md); font-weight: var(--fw-semibold); }

/* Section tabs */
.installed-tabs {
  display: flex;
  gap: var(--sp-1);
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.installed-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: var(--sp-2);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}

.installed-tab:hover { background: var(--color-surface-elevated); color: var(--color-text-primary); }

.installed-tab--active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.installed-tab-count {
  font-size: var(--text-xs);
  padding: 0 6px;
  border-radius: 999px;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
}

.installed-tab--active .installed-tab-count {
  background: rgba(59, 130, 246, 0.15);
  color: var(--color-accent);
}

/* Import zip */
.import-zip-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
}

.import-zip-btn { flex: 1; justify-content: center; }

.hidden-input { display: none; }

.zip-help {
  padding: var(--sp-3);
  border-bottom: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.zip-help code {
  background: var(--color-surface-elevated);
  padding: 1px 4px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
}

.zip-help-code {
  background: var(--color-bg);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  padding: var(--sp-2);
  font-size: 10px;
  line-height: 1.5;
  color: var(--color-text-secondary);
  overflow-x: auto;
  white-space: pre;
  margin: 0;
}

.zip-error {
  padding: var(--sp-2) var(--sp-3);
  color: var(--color-error);
  background: var(--color-error-subtle);
  flex-shrink: 0;
}

.panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-2);
}

.installed-loading { display: flex; justify-content: center; padding: var(--sp-6); color: var(--color-text-muted); }

.installed-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.installed-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-md);
  transition: background var(--t-fast);
}

.installed-item:hover { background: var(--color-surface-elevated); }

.avail-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}
.avail-dot--ok  { background: var(--color-success); }
.avail-dot--off { background: var(--color-text-muted); }

.installed-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.installed-name { font-size: var(--text-sm); font-weight: var(--fw-medium); }

.installed-tags,
.result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 2px;
}

.mini-chip {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
}

/* ── Browser panel (right) ───────────────────────────────── */
.browser-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.browser-header {
  padding: var(--sp-4) var(--sp-6);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.browser-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.browser-title { font-size: var(--text-xl); font-weight: var(--fw-semibold); }

/* Tabs */
.browser-tabs {
  display: flex;
  gap: var(--sp-1);
}

.browser-tab {
  padding: var(--sp-2) var(--sp-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast), border-color var(--t-fast);
}

.browser-tab:hover { background: var(--color-surface-elevated); color: var(--color-text-primary); }

.browser-tab--active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  border-color: var(--color-accent);
}

/* Search */
.search-row {
  display: flex;
  gap: var(--sp-2);
}

.search-input-wrap {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: var(--sp-3);
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  padding-left: 34px;
}

/* Param slider */
.param-filter {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.param-filter-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.param-value {
  font-size: var(--text-xs);
  font-weight: var(--fw-medium);
  color: var(--color-accent);
}

.param-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: var(--color-surface-elevated);
  outline: none;
  cursor: pointer;
}

.param-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-accent);
  cursor: pointer;
  border: 2px solid var(--color-bg);
}

.param-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--color-accent);
  cursor: pointer;
  border: 2px solid var(--color-bg);
}

.results-hint {
  list-style: none;
  padding: var(--sp-1) var(--sp-2) var(--sp-2);
}

.import-error { color: var(--color-error); }

/* Results */
.browser-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-5) var(--sp-6);
}

.results-loading {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-6);
  color: var(--color-text-muted);
}

.results-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  max-width: 860px;
}

.result-card {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  transition: border-color var(--t-fast);
}

.result-card:hover { border-color: var(--color-border); }

.result-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.result-top {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.result-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-name:hover { color: var(--color-accent); }

.result-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.result-stat strong { color: var(--color-text-secondary); font-weight: var(--fw-semibold); }

.result-action { flex-shrink: 0; }
</style>
