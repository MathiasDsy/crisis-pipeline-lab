<template>
  <div class="resources-view">
    <header class="res-header">
      <div>
        <h1>Resource Manager</h1>
        <p>CRUD des modèles, pipelines, datasets et suivi des runs.</p>
      </div>

      <button class="btn btn-primary" @click="createNew">
        + Nouveau {{ currentConfig.singular }}
      </button>
    </header>

    <main class="res-body">
      <aside class="res-sidebar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <small>{{ tab.count }}</small>
        </button>
      </aside>

      <section class="res-center">
        <div class="res-toolbar">
          <input v-model="search" class="search-input" placeholder="Rechercher..." />

          <select v-model="statusFilter" class="filter-select">
            <option value="">Tous</option>
            <option value="valid">Valides / disponibles</option>
            <option value="invalid">Invalides / indisponibles</option>
          </select>
        </div>

        <div class="res-table">
          <div class="res-table-head">
            <span v-for="field in currentConfig.columns" :key="field.key">
              {{ field.label }}
            </span>
          </div>

          <div
            v-for="item in filteredItems"
            :key="item.id"
            class="res-row"
            :class="{ active: selectedItem?.id === item.id }"
            @click="selectItem(item)"
          >
            <span v-for="field in currentConfig.columns" :key="field.key">
              <template v-if="field.type === 'badge'">
                <span class="badge" :class="item[field.key] ? 'badge-success' : 'badge-danger'">
                  {{ item[field.key] ? field.trueLabel : field.falseLabel }}
                </span>
              </template>

              <template v-else-if="field.type === 'date'">
                {{ formatDate(item[field.key]) }}
              </template>

              <template v-else>
                {{ item[field.key] ?? '—' }}
              </template>
            </span>
          </div>

          <div v-if="filteredItems.length === 0" class="empty-table">Aucun élément trouvé.</div>
        </div>
      </section>

      <aside class="res-detail">
        <div v-if="!selectedItem" class="detail-empty">
          <p>Sélectionne une ressource pour voir le détail.</p>
        </div>

        <div v-else class="detail-panel">
          <div class="detail-head">
            <div>
              <h2>{{ selectedItem.name || selectedItem.id }}</h2>
              <p>{{ currentConfig.singular }}</p>
            </div>

            <div class="detail-actions">
              <button class="icon-btn" @click="duplicateItem">⧉</button>
              <button class="icon-btn danger" @click="deleteItem">🗑</button>
            </div>
          </div>

          <div class="form-grid">
            <div v-for="field in currentConfig.formFields" :key="field.key" class="form-field">
              <label>{{ field.label }}</label>

              <input
                v-if="field.type === 'text'"
                v-model="editBuffer[field.key]"
                class="form-input"
              />

              <textarea
                v-else-if="field.type === 'textarea'"
                v-model="editBuffer[field.key]"
                class="form-textarea"
              />

              <select
                v-else-if="field.type === 'boolean'"
                v-model="editBuffer[field.key]"
                class="form-input"
              >
                <option :value="true">true</option>
                <option :value="false">false</option>
              </select>

              <textarea
                v-else-if="field.type === 'json'"
                v-model="jsonBuffers[field.key]"
                class="json-editor"
                spellcheck="false"
              />
            </div>
          </div>

          <div class="detail-footer">
            <button class="btn" @click="resetEdit">Reset</button>
            <button class="btn btn-primary" @click="saveItem">Sauvegarder</button>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const activeTab = ref('models')
const selectedItem = ref(null)
const editBuffer = ref({})
const jsonBuffers = ref({})
const search = ref('')
const statusFilter = ref('')

const data = ref({
  models: [
    {
      id: 'm1',
      name: 'GLiNER Location Extractor',
      model_key: 'gliner_location_v1',
      model_type: 'ner',
      compatible_components_key: ['location_extractor'],
      version: '1.0.0',
      local_path: '/models/gliner',
      is_available: true,
      metadata_json: {
        language: 'multilingual',
        task: 'location extraction',
      },
      created_at: '2026-06-20T12:00:00',
      updated_at: '2026-06-21T12:00:00',
    },
    {
      id: 'm2',
      name: 'Crisis Classifier',
      model_key: 'crisis_classifier_v1',
      model_type: 'classifier',
      compatible_components_key: ['noise_filter', 'signal_classifier'],
      version: '1.0.0',
      local_path: '/models/classifier',
      is_available: false,
      metadata_json: {
        labels: ['signal', 'noise'],
      },
      created_at: '2026-06-20T12:00:00',
      updated_at: '2026-06-21T12:00:00',
    },
  ],

  pipelines: [
    {
      id: 'p1',
      name: 'Pipeline Alpha',
      version: '1.0.0',
      description: 'Classifier → GLiNER → LLM judge → Event clustering',
      config_json: {
        steps: [
          {
            name: 'classifier',
            component: 'noise_filter',
            model_key: 'crisis_classifier_v1',
            threshold: 0.65,
          },
          {
            name: 'location_extraction',
            component: 'location_extractor',
            model_key: 'gliner_location_v1',
          },
          {
            name: 'llm_judge',
            component: 'source_location_judge',
            model_key: 'mistral_local',
          },
        ],
      },
      required_models_json: ['crisis_classifier_v1', 'gliner_location_v1', 'mistral_local'],
      required_components_json: ['noise_filter', 'location_extractor', 'source_location_judge'],
      original_filename: 'pipeline_alpha.json',
      is_valid: true,
      config_hash: 'abc123',
      validation_errors: [],
      created_at: '2026-06-20T12:00:00',
    },
  ],

  datasets: [
    {
      id: 'd1',
      name: 'Wildfire Dalmatia',
      path: '/datasets/wildfire_dalmatia.csv',
      hash: 'dataset_hash_123',
      is_valid: true,
      validation_errors: [],
      metadata_json: {
        rows: 10000,
        labels: {
          signal: 2400,
          noise: 7600,
        },
        language: 'en',
      },
      created_at: '2026-06-20T12:00:00',
      updated_at: '2026-06-21T12:00:00',
    },
  ],

  runs: [
    {
      id: 'r1',
      pipeline_config_id: 'p1',
      dataset_id: 'd1',
      mode: 'simulation',
      status: 'completed',
      started_at: '2026-06-21T10:00:00',
      finished_at: '2026-06-21T10:04:00',
      model_snapshot_json: {
        crisis_classifier_v1: '1.0.0',
        gliner_location_v1: '1.0.0',
      },
    },
  ],
})

const resourceConfigs = {
  models: {
    label: 'Models',
    singular: 'modèle',
    columns: [
      { key: 'name', label: 'Nom' },
      { key: 'model_key', label: 'Key' },
      { key: 'model_type', label: 'Type' },
      { key: 'version', label: 'Version' },
      {
        key: 'is_available',
        label: 'Status',
        type: 'badge',
        trueLabel: 'Available',
        falseLabel: 'Missing',
      },
    ],
    formFields: [
      { key: 'name', label: 'Nom', type: 'text' },
      { key: 'model_key', label: 'Model key', type: 'text' },
      { key: 'model_type', label: 'Model type', type: 'text' },
      { key: 'version', label: 'Version', type: 'text' },
      { key: 'local_path', label: 'Local path', type: 'text' },
      { key: 'is_available', label: 'Available', type: 'boolean' },
      { key: 'compatible_components_key', label: 'Compatible components JSON', type: 'json' },
      { key: 'metadata_json', label: 'Metadata JSON', type: 'json' },
    ],
  },

  pipelines: {
    label: 'Pipelines',
    singular: 'pipeline',
    columns: [
      { key: 'name', label: 'Nom' },
      { key: 'version', label: 'Version' },
      {
        key: 'is_valid',
        label: 'Validité',
        type: 'badge',
        trueLabel: 'Valid',
        falseLabel: 'Invalid',
      },
      { key: 'config_hash', label: 'Hash' },
      { key: 'created_at', label: 'Créé', type: 'date' },
    ],
    formFields: [
      { key: 'name', label: 'Nom', type: 'text' },
      { key: 'version', label: 'Version', type: 'text' },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'original_filename', label: 'Original filename', type: 'text' },
      { key: 'is_valid', label: 'Valid', type: 'boolean' },
      { key: 'config_json', label: 'Config JSON', type: 'json' },
      { key: 'required_models_json', label: 'Required models JSON', type: 'json' },
      { key: 'required_components_json', label: 'Required components JSON', type: 'json' },
      { key: 'validation_errors', label: 'Validation errors JSON', type: 'json' },
    ],
  },

  datasets: {
    label: 'Datasets',
    singular: 'dataset',
    columns: [
      { key: 'name', label: 'Nom' },
      { key: 'path', label: 'Path' },
      {
        key: 'is_valid',
        label: 'Validité',
        type: 'badge',
        trueLabel: 'Valid',
        falseLabel: 'Invalid',
      },
      { key: 'hash', label: 'Hash' },
      { key: 'updated_at', label: 'Modifié', type: 'date' },
    ],
    formFields: [
      { key: 'name', label: 'Nom', type: 'text' },
      { key: 'path', label: 'Path', type: 'text' },
      { key: 'hash', label: 'Hash', type: 'text' },
      { key: 'is_valid', label: 'Valid', type: 'boolean' },
      { key: 'metadata_json', label: 'Metadata JSON', type: 'json' },
      { key: 'validation_errors', label: 'Validation errors JSON', type: 'json' },
    ],
  },

  runs: {
    label: 'Runs',
    singular: 'run',
    columns: [
      { key: 'id', label: 'ID' },
      { key: 'mode', label: 'Mode' },
      { key: 'status', label: 'Status' },
      { key: 'started_at', label: 'Started', type: 'date' },
      { key: 'finished_at', label: 'Finished', type: 'date' },
    ],
    formFields: [
      { key: 'id', label: 'ID', type: 'text' },
      { key: 'pipeline_config_id', label: 'Pipeline config ID', type: 'text' },
      { key: 'dataset_id', label: 'Dataset ID', type: 'text' },
      { key: 'mode', label: 'Mode', type: 'text' },
      { key: 'status', label: 'Status', type: 'text' },
      { key: 'model_snapshot_json', label: 'Model snapshot JSON', type: 'json' },
    ],
  },
}

const currentConfig = computed(() => resourceConfigs[activeTab.value])

const tabs = computed(() => [
  { key: 'models', label: 'Models', count: data.value.models.length },
  { key: 'pipelines', label: 'Pipelines', count: data.value.pipelines.length },
  { key: 'datasets', label: 'Datasets', count: data.value.datasets.length },
  { key: 'runs', label: 'Runs', count: data.value.runs.length },
])

const currentItems = computed(() => data.value[activeTab.value] || [])

const filteredItems = computed(() => {
  const query = search.value.trim().toLowerCase()

  return currentItems.value.filter((item) => {
    const matchesSearch = !query || JSON.stringify(item).toLowerCase().includes(query)

    const statusKey =
      activeTab.value === 'models' ? 'is_available' : activeTab.value === 'runs' ? null : 'is_valid'

    const matchesStatus =
      !statusFilter.value ||
      !statusKey ||
      (statusFilter.value === 'valid' && item[statusKey]) ||
      (statusFilter.value === 'invalid' && !item[statusKey])

    return matchesSearch && matchesStatus
  })
})

function switchTab(tab) {
  activeTab.value = tab
  selectedItem.value = null
  editBuffer.value = {}
  jsonBuffers.value = {}
  search.value = ''
  statusFilter.value = ''
}

function selectItem(item) {
  selectedItem.value = item
  editBuffer.value = structuredClone(item)
  jsonBuffers.value = {}

  for (const field of currentConfig.value.formFields) {
    if (field.type === 'json') {
      jsonBuffers.value[field.key] = JSON.stringify(item[field.key] ?? {}, null, 2)
    }
  }
}

function createNew() {
  const now = new Date().toISOString()

  const base = {
    id: crypto.randomUUID(),
    name: `Nouveau ${currentConfig.value.singular}`,
    created_at: now,
    updated_at: now,
  }

  if (activeTab.value === 'models') {
    Object.assign(base, {
      model_key: '',
      model_type: '',
      compatible_components_key: [],
      version: '1.0.0',
      local_path: '',
      is_available: false,
      metadata_json: {},
    })
  }

  if (activeTab.value === 'pipelines') {
    Object.assign(base, {
      version: '1.0.0',
      description: '',
      config_json: { steps: [] },
      required_models_json: [],
      required_components_json: [],
      original_filename: '',
      is_valid: false,
      config_hash: '',
      validation_errors: [],
    })
  }

  if (activeTab.value === 'datasets') {
    Object.assign(base, {
      path: '',
      hash: '',
      is_valid: false,
      validation_errors: [],
      metadata_json: {},
    })
  }

  if (activeTab.value === 'runs') {
    Object.assign(base, {
      pipeline_config_id: '',
      dataset_id: '',
      mode: 'simulation',
      status: 'pending',
      started_at: now,
      finished_at: null,
      model_snapshot_json: {},
    })
  }

  data.value[activeTab.value].unshift(base)
  selectItem(base)
}

function saveItem() {
  const parsed = structuredClone(editBuffer.value)

  for (const field of currentConfig.value.formFields) {
    if (field.type === 'json') {
      try {
        parsed[field.key] = JSON.parse(jsonBuffers.value[field.key] || 'null')
      } catch {
        alert(`JSON invalide dans ${field.label}`)
        return
      }
    }
  }

  if ('updated_at' in parsed) {
    parsed.updated_at = new Date().toISOString()
  }

  const list = data.value[activeTab.value]
  const idx = list.findIndex((item) => item.id === parsed.id)

  if (idx !== -1) {
    list[idx] = parsed
  }

  selectItem(parsed)
}

function resetEdit() {
  if (selectedItem.value) {
    selectItem(selectedItem.value)
  }
}

function duplicateItem() {
  if (!selectedItem.value) return

  const copy = structuredClone(selectedItem.value)
  copy.id = crypto.randomUUID()
  copy.name = `${copy.name || 'Copy'} copy`

  if ('created_at' in copy) copy.created_at = new Date().toISOString()
  if ('updated_at' in copy) copy.updated_at = new Date().toISOString()

  data.value[activeTab.value].unshift(copy)
  selectItem(copy)
}

function deleteItem() {
  if (!selectedItem.value) return

  const ok = confirm(`Supprimer ${selectedItem.value.name || selectedItem.value.id} ?`)
  if (!ok) return

  data.value[activeTab.value] = data.value[activeTab.value].filter(
    (item) => item.id !== selectedItem.value.id,
  )

  selectedItem.value = null
  editBuffer.value = {}
  jsonBuffers.value = {}
}

function formatDate(value) {
  if (!value) return '—'

  return new Date(value).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.resources-view {
  height: 100vh;
  background: #0d1117;
  color: #e6edf3;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.res-header {
  background: #161b22;
  border-bottom: 1px solid #21262d;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.res-header h1 {
  font-size: 18px;
  margin: 0;
  color: #e6edf3;
}

.res-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #7d8590;
}

.res-body {
  flex: 1;
  display: grid;
  grid-template-columns: 210px 1fr 360px;
  overflow: hidden;
}

.res-sidebar {
  background: #161b22;
  border-right: 1px solid #21262d;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #7d8590;
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: 0.15s;
}

.tab-btn:hover {
  background: #21262d;
  color: #e6edf3;
}

.tab-btn.active {
  background: #1f6feb22;
  border-color: #1f6feb;
  color: #58a6ff;
}

.tab-btn small {
  background: #21262d;
  border: 1px solid #30363d;
  color: #e6edf3;
  border-radius: 12px;
  padding: 1px 7px;
  font-size: 11px;
}

.res-center {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 18px;
  gap: 12px;
}

.res-toolbar {
  display: flex;
  gap: 10px;
}

.search-input,
.filter-select,
.form-input,
.form-textarea,
.json-editor {
  background: #21262d;
  color: #e6edf3;
  border: 1px solid #30363d;
  border-radius: 6px;
  outline: none;
}

.search-input {
  flex: 1;
  padding: 9px 12px;
}

.filter-select {
  width: 200px;
  padding: 9px 10px;
}

.search-input:focus,
.filter-select:focus,
.form-input:focus,
.form-textarea:focus,
.json-editor:focus {
  border-color: #58a6ff;
}

.res-table {
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.res-table-head,
.res-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  align-items: center;
}

.res-table-head {
  padding: 10px 14px;
  background: #21262d;
  color: #7d8590;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid #30363d;
}

.res-row {
  padding: 11px 14px;
  border-bottom: 1px solid #21262d;
  cursor: pointer;
  font-size: 12px;
  color: #c9d1d9;
  transition: 0.15s;
}

.res-row:hover {
  background: #1c2128;
}

.res-row.active {
  background: #1f6feb18;
  outline: 1px solid #1f6feb;
  outline-offset: -1px;
}

.res-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 20px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
}

.badge-success {
  background: #0d2e1a;
  color: #3fb950;
  border: 1px solid #238636;
}

.badge-danger {
  background: #2d1f1f;
  color: #f87171;
  border: 1px solid #f87171;
}

.empty-table {
  padding: 40px;
  text-align: center;
  color: #7d8590;
  font-size: 13px;
}

.res-detail {
  background: #161b22;
  border-left: 1px solid #21262d;
  overflow-y: auto;
}

.detail-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7d8590;
  text-align: center;
  padding: 24px;
}

.detail-panel {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid #21262d;
  padding-bottom: 14px;
}

.detail-head h2 {
  margin: 0;
  font-size: 16px;
  color: #e6edf3;
}

.detail-head p {
  margin: 4px 0 0;
  font-size: 11px;
  color: #7d8590;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #21262d;
  color: #7d8590;
  border: 1px solid #30363d;
  cursor: pointer;
}

.icon-btn:hover {
  border-color: #58a6ff;
  color: #58a6ff;
}

.icon-btn.danger:hover {
  border-color: #f87171;
  color: #f87171;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
}

.form-input {
  padding: 8px 10px;
}

.form-textarea {
  padding: 8px 10px;
  min-height: 70px;
  resize: vertical;
}

.json-editor {
  padding: 10px;
  min-height: 140px;
  resize: vertical;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 11px;
  line-height: 1.45;
  color: #c9d1d9;
}

.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #21262d;
  padding-top: 14px;
}

.btn {
  border: 1px solid #30363d;
  background: #21262d;
  color: #e6edf3;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.15s;
}

.btn:hover {
  border-color: #58a6ff;
  color: #58a6ff;
}

.btn-primary {
  background: #1f6feb;
  border-color: #1f6feb;
  color: white;
}

.btn-primary:hover {
  background: #388bfd;
  border-color: #388bfd;
  color: white;
}

::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 2px;
}
</style>
