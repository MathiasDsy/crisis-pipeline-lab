<template>
  <div class="benchmark-view">
    <header class="bench-header">
      <div>
        <h1>Benchmarking Lab</h1>
        <p>
          Comparer N modèles × M datasets, analyser les erreurs et préparer des résultats
          scientifiques.
        </p>
      </div>

      <div class="bench-actions">
        <button class="btn">Importer résultats</button>
        <button class="btn btn-primary" @click="runBenchmark">Lancer benchmark</button>
      </div>
    </header>

    <section class="bench-config">
      <div class="selector-group">
        <label>Datasets</label>
        <select v-model="selectedDataset" class="select">
          <option value="all">Tous les datasets</option>
          <option v-for="d in datasets" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>

      <div class="selector-group">
        <label>Models</label>
        <select v-model="selectedModel" class="select">
          <option value="all">Tous les modèles</option>
          <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
      </div>

      <div class="selector-group">
        <label>Métrique principale</label>
        <select v-model="primaryMetric" class="select">
          <option value="f1">F1</option>
          <option value="recall">Recall</option>
          <option value="precision">Precision</option>
          <option value="accuracy">Accuracy</option>
        </select>
      </div>

      <div class="summary-card">
        <span>Runs</span>
        <strong>{{ filteredResults.length }}</strong>
      </div>

      <div class="summary-card">
        <span>Best model</span>
        <strong>{{ bestModel?.modelName || '—' }}</strong>
      </div>

      <div class="summary-card">
        <span>{{ primaryMetric.toUpperCase() }}</span>
        <strong>{{ bestModel ? formatPct(bestModel[primaryMetric]) : '—' }}</strong>
      </div>
    </section>

    <nav class="bench-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </nav>

    <main class="bench-body">
      <!-- LEADERBOARD -->
      <section v-if="activeTab === 'leaderboard'" class="panel">
        <div class="panel-head">
          <div>
            <h2>Leaderboard</h2>
            <p>Classement global des modèles par dataset.</p>
          </div>

          <input v-model="search" class="search-input" placeholder="Rechercher modèle/dataset..." />
        </div>

        <div class="table">
          <div class="table-head leaderboard-grid">
            <span>Model</span>
            <span>Dataset</span>
            <span>Precision</span>
            <span>Recall</span>
            <span>F1</span>
            <span>Accuracy</span>
            <span>Latency</span>
            <span>Status</span>
          </div>

          <div
            v-for="row in sortedLeaderboard"
            :key="row.id"
            class="table-row leaderboard-grid"
            :class="{ selected: selectedResult?.id === row.id }"
            @click="selectResult(row)"
          >
            <span class="strong">{{ row.modelName }}</span>
            <span>{{ row.datasetName }}</span>
            <span>{{ formatPct(row.precision) }}</span>
            <span>{{ formatPct(row.recall) }}</span>
            <span>{{ formatPct(row.f1) }}</span>
            <span>{{ formatPct(row.accuracy) }}</span>
            <span>{{ row.latency_ms }}ms</span>
            <span>
              <span
                class="badge"
                :class="
                  row.f1 >= 0.75
                    ? 'badge-success'
                    : row.f1 >= 0.55
                      ? 'badge-warning'
                      : 'badge-danger'
                "
              >
                {{ row.f1 >= 0.75 ? 'Strong' : row.f1 >= 0.55 ? 'Medium' : 'Weak' }}
              </span>
            </span>
          </div>
        </div>
      </section>

      <!-- ERROR ANALYSIS -->
      <section v-if="activeTab === 'errors'" class="panel">
        <div class="panel-head">
          <div>
            <h2>Error Analysis</h2>
            <p>Voir les tweets faciles, impossibles, instables et les erreurs fréquentes.</p>
          </div>

          <div class="filters-inline">
            <select v-model="errorFilter" class="select compact">
              <option value="all">Toutes les prédictions</option>
              <option value="fp">False positives</option>
              <option value="fn">False negatives</option>
              <option value="tp">True positives</option>
              <option value="tn">True negatives</option>
              <option value="never">Jamais détectés</option>
              <option value="always">Toujours détectés</option>
              <option value="unstable">Désaccord modèles</option>
            </select>
          </div>
        </div>

        <div class="error-layout">
          <aside class="error-sidebar">
            <div
              v-for="bucket in errorBuckets"
              :key="bucket.key"
              class="bucket-card"
              :class="{ active: errorFilter === bucket.key }"
              @click="errorFilter = bucket.key"
            >
              <span>{{ bucket.label }}</span>
              <strong>{{ bucket.count }}</strong>
            </div>
          </aside>

          <section class="tweet-list">
            <article
              v-for="tweet in filteredTweets.slice(0, 100)"
              :key="tweet.id"
              class="tweet-card"
              @click="selectedTweet = tweet"
            >
              <div class="tweet-card-head">
                <span class="tweet-id">#{{ tweet.shortId }}</span>
                <span class="badge" :class="tweetBadgeClass(tweet)">
                  {{ tweetVerdict(tweet) }}
                </span>
              </div>

              <p>{{ tweet.content }}</p>

              <div class="tweet-meta">
                <span
                  >Label: <strong>{{ tweet.label ? 'signal' : 'noise' }}</strong></span
                >
                <span
                  >Detected by:
                  <strong>{{ tweet.detectedBy.length }}/{{ models.length }}</strong></span
                >
                <span
                  >Difficulty: <strong>{{ tweetDifficulty(tweet) }}</strong></span
                >
              </div>
            </article>

            <div v-if="filteredTweets.length > 100" class="limit-note">
              Affichage limité à 100 tweets sur {{ filteredTweets.length }}.
            </div>
          </section>
        </div>
      </section>

      <!-- AGREEMENT -->
      <section v-if="activeTab === 'agreement'" class="panel">
        <div class="panel-head">
          <div>
            <h2>Model Agreement</h2>
            <p>Comprendre quels modèles se ressemblent, se complètent ou échouent ensemble.</p>
          </div>
        </div>

        <div class="matrix">
          <div class="matrix-corner"></div>
          <div v-for="m in models" :key="m.id" class="matrix-label top">{{ m.short }}</div>

          <template v-for="a in models" :key="a.id">
            <div class="matrix-label left">{{ a.short }}</div>
            <div
              v-for="b in models"
              :key="a.id + '-' + b.id"
              class="matrix-cell"
              :class="agreementClass(agreement(a.id, b.id))"
            >
              {{ formatPct(agreement(a.id, b.id)) }}
            </div>
          </template>
        </div>

        <div class="insight-grid">
          <div class="insight-card">
            <span>Most similar</span>
            <strong>{{ mostSimilar }}</strong>
          </div>
          <div class="insight-card">
            <span>Most complementary</span>
            <strong>{{ mostComplementary }}</strong>
          </div>
          <div class="insight-card">
            <span>Shared failures</span>
            <strong>{{ sharedFailures }}</strong>
          </div>
        </div>
      </section>

      <!-- DATASET DIFFICULTY -->
      <section v-if="activeTab === 'datasets'" class="panel">
        <div class="panel-head">
          <div>
            <h2>Dataset Difficulty</h2>
            <p>Identifier quels datasets sont faciles, bruités, ambigus ou trop déséquilibrés.</p>
          </div>
        </div>

        <div class="dataset-grid">
          <article v-for="d in datasetDifficulty" :key="d.id" class="dataset-card">
            <div class="dataset-card-head">
              <h3>{{ d.name }}</h3>
              <span
                class="badge"
                :class="
                  d.avgF1 >= 0.75
                    ? 'badge-success'
                    : d.avgF1 >= 0.55
                      ? 'badge-warning'
                      : 'badge-danger'
                "
              >
                {{ d.avgF1 >= 0.75 ? 'Easy' : d.avgF1 >= 0.55 ? 'Medium' : 'Hard' }}
              </span>
            </div>

            <div class="metric-line">
              <span>Avg F1</span>
              <strong>{{ formatPct(d.avgF1) }}</strong>
            </div>

            <div class="metric-line">
              <span>Avg Recall</span>
              <strong>{{ formatPct(d.avgRecall) }}</strong>
            </div>

            <div class="metric-line">
              <span>Never detected</span>
              <strong>{{ d.neverDetected }}</strong>
            </div>

            <div class="metric-line">
              <span>Model disagreement</span>
              <strong>{{ formatPct(d.disagreement) }}</strong>
            </div>

            <div class="bar">
              <div class="bar-fill" :style="{ width: d.avgF1 * 100 + '%' }"></div>
            </div>
          </article>
        </div>
      </section>
    </main>

    <aside class="detail-drawer" v-if="selectedResult || selectedTweet">
      <div class="drawer-head">
        <h2>{{ selectedTweet ? 'Tweet detail' : 'Benchmark detail' }}</h2>
        <button class="icon-btn" @click="closeDrawer">×</button>
      </div>

      <div v-if="selectedResult" class="drawer-section">
        <h3>{{ selectedResult.modelName }}</h3>
        <p>{{ selectedResult.datasetName }}</p>

        <div class="metric-grid">
          <div>
            <span>Precision</span><strong>{{ formatPct(selectedResult.precision) }}</strong>
          </div>
          <div>
            <span>Recall</span><strong>{{ formatPct(selectedResult.recall) }}</strong>
          </div>
          <div>
            <span>F1</span><strong>{{ formatPct(selectedResult.f1) }}</strong>
          </div>
          <div>
            <span>Accuracy</span><strong>{{ formatPct(selectedResult.accuracy) }}</strong>
          </div>
        </div>

        <pre>{{ JSON.stringify(selectedResult.confusion, null, 2) }}</pre>
      </div>

      <div v-if="selectedTweet" class="drawer-section">
        <h3>Tweet #{{ selectedTweet.shortId }}</h3>
        <p class="tweet-full">{{ selectedTweet.content }}</p>

        <div class="metric-line">
          <span>Ground truth</span>
          <strong>{{ selectedTweet.label ? 'signal' : 'noise' }}</strong>
        </div>

        <div class="model-pred-list">
          <div v-for="pred in selectedTweet.predictions" :key="pred.modelId" class="model-pred">
            <span>{{ modelName(pred.modelId) }}</span>
            <strong :class="pred.prediction ? 'text-signal' : 'text-muted'">
              {{ pred.prediction ? 'signal' : 'noise' }} · {{ formatPct(pred.score) }}
            </strong>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const activeTab = ref('leaderboard')
const selectedDataset = ref('all')
const selectedModel = ref('all')
const primaryMetric = ref('f1')
const search = ref('')
const errorFilter = ref('all')
const selectedResult = ref(null)
const selectedTweet = ref(null)

const tabs = [
  { key: 'leaderboard', label: 'Leaderboard' },
  { key: 'errors', label: 'Error Analysis' },
  { key: 'agreement', label: 'Model Agreement' },
  { key: 'datasets', label: 'Dataset Difficulty' },
]

const datasets = ref([
  { id: 'd1', name: 'Wildfire Dalmatia' },
  { id: 'd2', name: 'Earthquake Croatia' },
  { id: 'd3', name: 'Flood Balkans' },
])

const models = ref([
  { id: 'm1', name: 'Crisis Classifier v1', short: 'CC-v1' },
  { id: 'm2', name: 'MiniLM Classifier', short: 'MiniLM' },
  { id: 'm3', name: 'DistilBERT Crisis', short: 'Distil' },
  { id: 'm4', name: 'LLM Zero-shot Judge', short: 'LLM' },
])

const benchmarkResults = ref([
  row('m1', 'd1', 0.81, 0.74, 0.77, 0.88, 42),
  row('m2', 'd1', 0.75, 0.83, 0.79, 0.86, 26),
  row('m3', 'd1', 0.86, 0.69, 0.77, 0.89, 35),
  row('m4', 'd1', 0.71, 0.91, 0.8, 0.84, 420),

  row('m1', 'd2', 0.78, 0.7, 0.74, 0.85, 40),
  row('m2', 'd2', 0.69, 0.76, 0.72, 0.81, 25),
  row('m3', 'd2', 0.82, 0.66, 0.73, 0.86, 36),
  row('m4', 'd2', 0.73, 0.88, 0.8, 0.83, 430),

  row('m1', 'd3', 0.66, 0.61, 0.63, 0.78, 41),
  row('m2', 'd3', 0.62, 0.72, 0.67, 0.76, 24),
  row('m3', 'd3', 0.7, 0.58, 0.63, 0.8, 34),
  row('m4', 'd3', 0.64, 0.81, 0.71, 0.77, 450),
])

const tweets = ref(generateTweets())

const filteredResults = computed(() => {
  const q = search.value.trim().toLowerCase()

  return benchmarkResults.value.filter((r) => {
    const matchesDataset = selectedDataset.value === 'all' || r.datasetId === selectedDataset.value
    const matchesModel = selectedModel.value === 'all' || r.modelId === selectedModel.value
    const matchesSearch = !q || `${r.modelName} ${r.datasetName}`.toLowerCase().includes(q)

    return matchesDataset && matchesModel && matchesSearch
  })
})

const sortedLeaderboard = computed(() =>
  [...filteredResults.value].sort((a, b) => b[primaryMetric.value] - a[primaryMetric.value]),
)

const bestModel = computed(() => sortedLeaderboard.value[0] || null)

const filteredTweets = computed(() => {
  let list = tweets.value

  if (selectedDataset.value !== 'all') {
    list = list.filter((t) => t.datasetId === selectedDataset.value)
  }

  if (selectedModel.value !== 'all') {
    list = list.map((t) => ({
      ...t,
      predictions: t.predictions.filter((p) => p.modelId === selectedModel.value),
    }))
  }

  if (errorFilter.value === 'all') return list

  if (errorFilter.value === 'fp')
    return list.filter((t) => t.predictions.some((p) => p.prediction && !t.label))
  if (errorFilter.value === 'fn')
    return list.filter((t) => t.predictions.some((p) => !p.prediction && t.label))
  if (errorFilter.value === 'tp')
    return list.filter((t) => t.predictions.some((p) => p.prediction && t.label))
  if (errorFilter.value === 'tn')
    return list.filter((t) => t.predictions.some((p) => !p.prediction && !t.label))
  if (errorFilter.value === 'never') return list.filter((t) => t.label && t.detectedBy.length === 0)
  if (errorFilter.value === 'always')
    return list.filter((t) => t.label && t.detectedBy.length === models.value.length)
  if (errorFilter.value === 'unstable')
    return list.filter((t) => t.detectedBy.length > 0 && t.detectedBy.length < models.value.length)

  return list
})

const errorBuckets = computed(() => [
  { key: 'all', label: 'Tous', count: tweets.value.length },
  {
    key: 'fp',
    label: 'False positives',
    count: tweets.value.filter((t) => t.predictions.some((p) => p.prediction && !t.label)).length,
  },
  {
    key: 'fn',
    label: 'False negatives',
    count: tweets.value.filter((t) => t.predictions.some((p) => !p.prediction && t.label)).length,
  },
  {
    key: 'never',
    label: 'Jamais détectés',
    count: tweets.value.filter((t) => t.label && t.detectedBy.length === 0).length,
  },
  {
    key: 'always',
    label: 'Toujours détectés',
    count: tweets.value.filter((t) => t.label && t.detectedBy.length === models.value.length)
      .length,
  },
  {
    key: 'unstable',
    label: 'Désaccord modèles',
    count: tweets.value.filter(
      (t) => t.detectedBy.length > 0 && t.detectedBy.length < models.value.length,
    ).length,
  },
])

const datasetDifficulty = computed(() => {
  return datasets.value.map((d) => {
    const rows = benchmarkResults.value.filter((r) => r.datasetId === d.id)
    const dsTweets = tweets.value.filter((t) => t.datasetId === d.id)

    return {
      id: d.id,
      name: d.name,
      avgF1: avg(rows.map((r) => r.f1)),
      avgRecall: avg(rows.map((r) => r.recall)),
      neverDetected: dsTweets.filter((t) => t.label && t.detectedBy.length === 0).length,
      disagreement: avg(
        dsTweets.map((t) => {
          const ratio = t.detectedBy.length / models.value.length
          return ratio > 0 && ratio < 1 ? 1 : 0
        }),
      ),
    }
  })
})

const mostSimilar = computed(() => {
  let best = null

  for (const a of models.value) {
    for (const b of models.value) {
      if (a.id === b.id) continue
      const val = agreement(a.id, b.id)
      if (!best || val > best.val) best = { label: `${a.short} / ${b.short}`, val }
    }
  }

  return best ? `${best.label} (${formatPct(best.val)})` : '—'
})

const mostComplementary = computed(() => {
  let best = null

  for (const a of models.value) {
    for (const b of models.value) {
      if (a.id === b.id) continue
      const val = agreement(a.id, b.id)
      if (!best || val < best.val) best = { label: `${a.short} / ${b.short}`, val }
    }
  }

  return best ? `${best.label} (${formatPct(best.val)})` : '—'
})

const sharedFailures = computed(
  () => tweets.value.filter((t) => t.label && t.detectedBy.length === 0).length,
)

function row(modelId, datasetId, precision, recall, f1, accuracy, latency_ms) {
  const model = models.value.find((m) => m.id === modelId)
  const dataset = datasets.value.find((d) => d.id === datasetId)

  return {
    id: `${modelId}-${datasetId}`,
    modelId,
    datasetId,
    modelName: model?.name,
    datasetName: dataset?.name,
    precision,
    recall,
    f1,
    accuracy,
    latency_ms,
    confusion: {
      TP: Math.round(recall * 250),
      FP: Math.round((1 - precision) * 180),
      FN: Math.round((1 - recall) * 250),
      TN: Math.round(accuracy * 600),
    },
  }
}

function generateTweets() {
  const samples = [
    'Smoke visible near the pine forest north of Split, strong smell in the air.',
    'Firefighters are moving toward the hill, people are leaving the area.',
    'I just saw a movie about wildfires, insane visuals.',
    'Heavy smoke near the road, traffic stopped.',
    'Concert smoke machine was crazy tonight.',
    'Flames reported behind the village, emergency sirens active.',
    'Beautiful sunset in Dalmatia today.',
    'People are saying there is a fire but I cannot see anything.',
    'Ash falling on cars near the coast.',
    'The word wildfire is trending because of a video game.',
  ]

  return Array.from({ length: 260 }, (_, i) => {
    const dataset = datasets.value[i % datasets.value.length]
    const label = [0, 1, 3, 5, 8].includes(i % 10)

    const predictions = models.value.map((m, idx) => {
      const noise = ((i * (idx + 3)) % 10) / 100
      const base = label ? 0.62 + idx * 0.04 : 0.28 + idx * 0.03
      const score = Math.min(0.98, Math.max(0.02, base + noise - (i % 7 === 0 ? 0.28 : 0)))
      return {
        modelId: m.id,
        prediction: score >= 0.5,
        score,
      }
    })

    const detectedBy = predictions.filter((p) => p.prediction).map((p) => p.modelId)

    return {
      id: crypto.randomUUID(),
      shortId: String(i + 1).padStart(4, '0'),
      datasetId: dataset.id,
      content: samples[i % samples.length],
      label,
      predictions,
      detectedBy,
    }
  })
}

function agreement(modelA, modelB) {
  const same = tweets.value.filter((t) => {
    const a = t.predictions.find((p) => p.modelId === modelA)?.prediction
    const b = t.predictions.find((p) => p.modelId === modelB)?.prediction
    return a === b
  }).length

  return same / tweets.value.length
}

function agreementClass(value) {
  if (value >= 0.85) return 'cell-high'
  if (value >= 0.65) return 'cell-mid'
  return 'cell-low'
}

function avg(values) {
  if (!values.length) return 0
  return values.reduce((a, b) => a + b, 0) / values.length
}

function modelName(id) {
  return models.value.find((m) => m.id === id)?.name || id
}

function formatPct(value) {
  return `${Math.round(value * 100)}%`
}

function selectResult(row) {
  selectedResult.value = row
  selectedTweet.value = null
}

function closeDrawer() {
  selectedResult.value = null
  selectedTweet.value = null
}

function runBenchmark() {
  alert('TODO: connecter à ton endpoint backend de benchmark.')
}

function tweetVerdict(tweet) {
  const detected = tweet.detectedBy.length

  if (tweet.label && detected === models.value.length) return 'always detected'
  if (tweet.label && detected === 0) return 'never detected'
  if (detected > 0 && detected < models.value.length) return 'unstable'
  if (!tweet.label && detected > 0) return 'false positive risk'
  return 'stable'
}

function tweetBadgeClass(tweet) {
  const verdict = tweetVerdict(tweet)
  if (verdict === 'always detected') return 'badge-success'
  if (verdict === 'never detected') return 'badge-danger'
  if (verdict === 'unstable') return 'badge-warning'
  if (verdict === 'false positive risk') return 'badge-danger'
  return 'badge-muted'
}

function tweetDifficulty(tweet) {
  if (tweet.label && tweet.detectedBy.length === 0) return 'hard'
  if (tweet.detectedBy.length > 0 && tweet.detectedBy.length < models.value.length)
    return 'ambiguous'
  return 'easy'
}
</script>

<style scoped>
.benchmark-view {
  height: 100vh;
  background: #0d1117;
  color: #e6edf3;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.bench-header {
  background: #161b22;
  border-bottom: 1px solid #21262d;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bench-header h1,
.panel h2 {
  margin: 0;
  font-size: 18px;
}

.bench-header p,
.panel-head p {
  margin: 4px 0 0;
  color: #7d8590;
  font-size: 12px;
}

.bench-actions,
.filters-inline {
  display: flex;
  gap: 10px;
}

.bench-config {
  background: #161b22;
  border-bottom: 1px solid #21262d;
  padding: 12px 24px;
  display: flex;
  align-items: end;
  gap: 14px;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.selector-group label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
}

.select,
.search-input {
  background: #21262d;
  color: #e6edf3;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 8px 10px;
  outline: none;
}

.select {
  min-width: 190px;
}

.select.compact {
  min-width: 220px;
}

.search-input {
  min-width: 260px;
}

.select:focus,
.search-input:focus {
  border-color: #58a6ff;
}

.summary-card {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 8px 12px;
  min-width: 110px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-card span {
  color: #7d8590;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-card strong {
  font-size: 14px;
}

.bench-tabs {
  background: #0d1117;
  border-bottom: 1px solid #21262d;
  padding: 10px 24px 0;
  display: flex;
  gap: 8px;
}

.tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #7d8590;
  padding: 9px 14px;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  font-size: 12px;
}

.tab-btn:hover {
  color: #e6edf3;
  background: #161b22;
}

.tab-btn.active {
  background: #161b22;
  border-color: #21262d;
  border-bottom-color: #161b22;
  color: #58a6ff;
}

.bench-body {
  flex: 1;
  overflow: hidden;
  padding: 18px;
}

.panel {
  height: 100%;
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-head {
  padding: 16px;
  border-bottom: 1px solid #21262d;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table {
  overflow-y: auto;
}

.table-head,
.table-row {
  display: grid;
  gap: 12px;
  align-items: center;
}

.leaderboard-grid {
  grid-template-columns: 1.4fr 1.2fr repeat(5, 0.7fr) 0.8fr;
}

.table-head {
  background: #21262d;
  color: #7d8590;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 10px 14px;
  border-bottom: 1px solid #30363d;
}

.table-row {
  padding: 12px 14px;
  border-bottom: 1px solid #21262d;
  cursor: pointer;
  color: #c9d1d9;
  font-size: 12px;
}

.table-row:hover {
  background: #1c2128;
}

.table-row.selected {
  background: #1f6feb18;
  outline: 1px solid #1f6feb;
  outline-offset: -1px;
}

.strong {
  color: #e6edf3;
  font-weight: 600;
}

.badge {
  display: inline-flex;
  border-radius: 20px;
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 700;
  border: 1px solid transparent;
  white-space: nowrap;
}

.badge-success {
  background: #0d2e1a;
  color: #3fb950;
  border-color: #238636;
}

.badge-warning {
  background: #2d1f00;
  color: #e3b341;
  border-color: #9e6a03;
}

.badge-danger {
  background: #2d1f1f;
  color: #f87171;
  border-color: #f87171;
}

.badge-muted {
  background: #21262d;
  color: #7d8590;
  border-color: #30363d;
}

.error-layout {
  display: grid;
  grid-template-columns: 230px 1fr;
  overflow: hidden;
  flex: 1;
}

.error-sidebar {
  border-right: 1px solid #21262d;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.bucket-card {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  color: #c9d1d9;
  font-size: 12px;
}

.bucket-card:hover,
.bucket-card.active {
  border-color: #58a6ff;
  color: #58a6ff;
}

.tweet-list {
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tweet-card {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
}

.tweet-card:hover {
  border-color: #58a6ff;
}

.tweet-card-head,
.tweet-meta,
.metric-line,
.model-pred {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.tweet-id {
  color: #7d8590;
  font-size: 11px;
}

.tweet-card p {
  margin: 10px 0;
  line-height: 1.45;
  font-size: 13px;
}

.tweet-meta {
  color: #7d8590;
  font-size: 11px;
}

.limit-note {
  text-align: center;
  color: #7d8590;
  font-size: 12px;
  padding: 12px;
}

.matrix {
  display: grid;
  grid-template-columns: 90px repeat(4, 1fr);
  gap: 1px;
  padding: 18px;
}

.matrix-corner,
.matrix-label,
.matrix-cell {
  background: #21262d;
  border: 1px solid #30363d;
  padding: 14px;
  text-align: center;
  font-size: 12px;
}

.matrix-label {
  color: #7d8590;
  font-weight: 700;
}

.matrix-cell {
  font-weight: 800;
}

.cell-high {
  color: #3fb950;
}

.cell-mid {
  color: #e3b341;
}

.cell-low {
  color: #f87171;
}

.insight-grid,
.dataset-grid {
  padding: 18px;
  display: grid;
  gap: 14px;
}

.insight-grid {
  grid-template-columns: repeat(3, 1fr);
}

.dataset-grid {
  grid-template-columns: repeat(3, 1fr);
  overflow-y: auto;
}

.insight-card,
.dataset-card {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 14px;
}

.insight-card span {
  display: block;
  color: #7d8590;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}

.dataset-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dataset-card h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

.metric-line {
  color: #7d8590;
  font-size: 12px;
  margin: 8px 0;
}

.metric-line strong {
  color: #e6edf3;
}

.bar {
  height: 5px;
  background: #161b22;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 12px;
}

.bar-fill {
  height: 100%;
  background: #58a6ff;
}

.detail-drawer {
  position: absolute;
  right: 0;
  top: 0;
  width: 380px;
  height: 100%;
  background: #161b22;
  border-left: 1px solid #21262d;
  box-shadow: -20px 0 40px #00000055;
  overflow-y: auto;
  z-index: 20;
}

.drawer-head {
  padding: 16px;
  border-bottom: 1px solid #21262d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-head h2 {
  margin: 0;
  font-size: 16px;
}

.drawer-section {
  padding: 16px;
}

.drawer-section h3 {
  margin: 0 0 4px;
  font-size: 15px;
}

.drawer-section p {
  color: #7d8590;
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 16px 0;
}

.metric-grid div {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 10px;
}

.metric-grid span {
  display: block;
  color: #7d8590;
  font-size: 10px;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.metric-grid strong {
  font-size: 18px;
}

pre {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  color: #c9d1d9;
  font-size: 11px;
  overflow-x: auto;
}

.tweet-full {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  line-height: 1.5;
  color: #e6edf3 !important;
}

.model-pred-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}

.model-pred {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 10px;
  font-size: 12px;
}

.text-signal {
  color: #f87171;
}

.text-muted {
  color: #7d8590;
}

.btn,
.icon-btn {
  border: 1px solid #30363d;
  background: #21262d;
  color: #e6edf3;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.15s;
}

.btn {
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
}

.icon-btn {
  width: 30px;
  height: 30px;
  font-size: 18px;
}

.btn:hover,
.icon-btn:hover {
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
