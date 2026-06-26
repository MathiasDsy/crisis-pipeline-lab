<template>
  <div class="simulation-view">
    <!-- Header: Dataset + Pipeline selectors -->
    <header class="sim-header">
      <div class="sim-header__selectors">
        <div class="selector-group">
          <label class="selector-label">Dataset</label>
          <select v-model="selectedDataset" class="sim-select" @change="checkSimulation">
            <option value="">— Choisir un dataset —</option>
            <option v-for="d in datasets" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </div>

        <div class="selector-sep">×</div>

        <div class="selector-group">
          <label class="selector-label">Pipeline</label>
          <select v-model="selectedPipeline" class="sim-select" @change="checkSimulation">
            <option value="">— Choisir un pipeline —</option>
            <option v-for="p in pipelines" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>

        <div v-if="simulationStatus !== null" class="sim-status-badge" :class="simulationStatus ? 'badge--ready' : 'badge--missing'">
          <span class="badge-dot"></span>
          {{ simulationStatus ? 'Simulation disponible' : 'Pas encore simulé' }}
          <button v-if="!simulationStatus" class="btn-run" @click="runSimulation">Lancer</button>
        </div>
      </div>

      <div class="sim-header__counters" v-if="simulationLoaded">
        <span class="counter">Tweets <strong>{{ currentIndex }}</strong> / {{ tweets.length }}</span>
        <span class="counter-sep">·</span>
        <span class="counter">Signaux <strong class="text-signal">{{ signalsDetected }}</strong></span>
        <span class="counter-sep">·</span>
        <span class="counter">Utiles (labels) <strong class="text-useful">{{ usefulLabeled }}</strong></span>
        <span class="counter-sep">·</span>
        <span class="counter">Overlap <strong class="text-overlap">{{ overlap }}</strong></span>
      </div>
    </header>

    <!-- Main 3-column layout -->
    <main class="sim-body" v-if="simulationLoaded">

      <!-- LEFT: Controls + Events -->
      <aside class="sim-col sim-col--left">
        <!-- Playback controls -->
        <div class="controls-block">
          <div class="controls-btns">
            <button class="ctrl-btn" @click="reset" title="Reset">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/></svg>
            </button>
            <button class="ctrl-btn ctrl-btn--play" @click="togglePlay" :title="isPlaying ? 'Pause' : 'Play'">
              <svg v-if="!isPlaying" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
            </button>
          </div>
          <div class="speed-pills">
            <button v-for="s in speeds" :key="s" class="speed-pill" :class="{ active: currentSpeed === s }" @click="currentSpeed = s">×{{ s }}</button>
          </div>
        </div>

        <!-- Events list -->
        <div class="events-block">
          <div class="events-header">
            <span class="events-title">Events détectés</span>
            <span class="events-count">{{ visibleEvents.length }}</span>
          </div>
          <div class="events-list">
            <div
              v-for="event in visibleEvents"
              :key="event.id"
              class="event-card"
              :class="{ 'event-card--active': activeEventId === event.id }"
              @click="selectEvent(event)"
            >
              <div class="event-card__name">{{ event.name }}</div>
              <div class="event-card__meta">
                <span class="event-location">📍 {{ event.location }}</span>
                <span class="event-tweets">{{ event.tweetIds.length }} tweets</span>
              </div>
            </div>
            <div v-if="visibleEvents.length === 0" class="events-empty">Aucun event détecté</div>
          </div>
        </div>
      </aside>

      <!-- CENTER: Timeline + Map -->
      <section class="sim-col sim-col--center">

        <!-- Timeline -->
        <div class="timeline-block">
          <div class="timeline-label">Timeline des tweets</div>
          <div class="timeline-track" ref="trackRef" @click="onTrackClick">
            <!-- Read head -->
            <div class="timeline-readhead" :style="{ left: readHeadPercent + '%' }"></div>

            <!-- Tweet dots -->
            <div
              v-for="(tweet, idx) in tweets"
              :key="tweet.id"
              class="tweet-dot"
              :class="tweetDotClass(tweet, idx)"
              :style="{ left: (idx / (tweets.length - 1)) * 100 + '%' }"
              :title="'Tweet #' + (idx + 1)"
              @click.stop="selectTweet(tweet, idx)"
            ></div>
          </div>

          <!-- Legend -->
          <div class="timeline-legend">
            <span class="legend-item"><span class="legend-dot legend-dot--signal"></span>Signal détecté</span>
            <span class="legend-item"><span class="legend-dot legend-dot--useful"></span>Utile (label)</span>
            <span class="legend-item"><span class="legend-dot legend-dot--both"></span>Les deux</span>
            <span class="legend-item"><span class="legend-dot legend-dot--none"></span>No signal</span>
          </div>
        </div>

        <!-- Mini Map -->
        <div class="map-block">
          <div id="sim-map" ref="mapRef"></div>
          <div class="map-label">Localisation des events géolocalisés</div>
        </div>
      </section>

      <!-- RIGHT: Tweet detail panel -->
      <aside class="sim-col sim-col--right">
        <div v-if="!selectedTweet" class="detail-empty">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p>Cliquez sur un tweet<br>pour voir le détail</p>
        </div>

        <div v-else class="detail-panel">
          <div class="detail-tweet-index">Tweet #{{ selectedTweetIndex + 1 }}</div>

          <div class="detail-text">{{ selectedTweet.text }}</div>

          <div class="detail-location">
            <span v-if="selectedTweet.location" class="location-badge">📍 {{ selectedTweet.location }}</span>
            <span v-else class="location-badge location-badge--none">Non localisé</span>
          </div>

          <!-- Cascade -->
          <div class="detail-section-title">Cascade de modèles</div>
          <div class="cascade">
            <div v-for="(step, i) in selectedTweet.cascade" :key="i" class="cascade-step">
              <div class="cascade-step__left">
                <span class="cascade-index">{{ i + 1 }}</span>
                <span class="cascade-model">{{ step.model }}</span>
              </div>
              <div class="cascade-step__right">
                <div class="cascade-bar">
                  <div class="cascade-bar__fill" :style="{ width: (step.score * 100) + '%', background: scoreColor(step.score) }"></div>
                </div>
                <span class="cascade-score" :style="{ color: scoreColor(step.score) }">{{ (step.score * 100).toFixed(0) }}%</span>
                <span class="cascade-verdict" :class="step.pass ? 'pass' : 'fail'">{{ step.pass ? '✓' : '✗' }}</span>
              </div>
            </div>
          </div>

          <!-- Final verdict -->
          <div class="detail-verdict" :class="selectedTweet.isSignal ? 'verdict--signal' : 'verdict--none'">
            {{ selectedTweet.isSignal ? '🔴 Signal détecté' : '⚫ No signal' }}
          </div>

          <!-- Label -->
          <div v-if="selectedTweet.label !== undefined" class="detail-label">
            <span class="label-title">Label dataset :</span>
            <span :class="selectedTweet.label ? 'label--useful' : 'label--notuseful'">
              {{ selectedTweet.label ? '✅ Utile à la crise' : '✗ Non utile' }}
            </span>
          </div>
        </div>
      </aside>
    </main>

    <!-- Empty state -->
    <div v-if="!simulationLoaded" class="sim-empty">
      <p>Sélectionnez un dataset et un pipeline pour commencer.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

// ─── MOCK DATA ────────────────────────────────────────────────────────────────

const datasets = ref([
  { id: 1, name: 'Croatia Earthquake 2023' },
  { id: 2, name: 'Flood Reports Balkans' },
  { id: 3, name: 'Wildfire Dalmatia' },
])

const pipelines = ref([
  { id: 1, name: 'Pipeline Alpha (classifier → LLM)' },
  { id: 2, name: 'Pipeline Beta (GliNER → classifier)' },
  { id: 3, name: 'Pipeline Gamma (full stack)' },
])

// Simulated results already computed by the backend
const mockSimulationResult = {
  tweets: Array.from({ length: 80 }, (_, i) => {
    const isSignal = Math.random() > 0.55
    const isUseful = Math.random() > 0.5
    const locations = ['Zagreb', 'Split', 'Dubrovnik', 'Rijeka', 'Osijek', null, null, null]
    const location = locations[Math.floor(Math.random() * locations.length)]
    return {
      id: i,
      text: [
        'Forte secousse ressentie à Zagreb, les gens dans la rue #séisme',
        'Des fissures apparaissent sur les murs après le tremblement de terre',
        'Évacuation en cours dans le centre ville, sirènes actives',
        'Mon immeuble tremble depuis 30 secondes, j\'ai peur',
        'Route coupée entre Zagreb et Split suite aux glissements',
        'Les équipes de secours arrivent à Petrinja',
        'La météo est belle aujourd\'hui à Split',
        'Nouveau restaurant ouvert près du port',
      ][Math.floor(Math.random() * 8)],
      isSignal,
      label: isUseful,
      location,
      cascade: [
        { model: 'Classifier', score: isSignal ? 0.6 + Math.random() * 0.35 : 0.1 + Math.random() * 0.4, pass: isSignal || Math.random() > 0.7 },
        { model: 'GliNER', score: location ? 0.7 + Math.random() * 0.25 : 0.1 + Math.random() * 0.3, pass: !!location },
        { model: 'LLM Scorer', score: isSignal ? 0.65 + Math.random() * 0.3 : 0.05 + Math.random() * 0.35, pass: isSignal },
      ],
    }
  }),
  events: [
    { id: 1, name: 'Séisme Zagreb M5.4', location: 'Zagreb', lat: 45.815, lng: 15.982, tweetIds: [0, 2, 5, 12, 18] },
    { id: 2, name: 'Glissement terrain Split', location: 'Split', lat: 43.508, lng: 16.440, tweetIds: [3, 9, 22] },
    { id: 3, name: 'Évacuation Petrinja', location: 'Petrinja', lat: 45.443, lng: 16.285, tweetIds: [7, 14, 31, 45] },
    { id: 4, name: 'Dommages structurels Rijeka', location: 'Rijeka', lat: 45.327, lng: 14.442, tweetIds: [1, 6, 28] },
  ],
}

// Simulate which pairs have already been run
const simulatedPairs = ref(new Set(['1-1', '1-2', '2-1']))

// ─── STATE ────────────────────────────────────────────────────────────────────

const selectedDataset = ref('')
const selectedPipeline = ref('')
const simulationStatus = ref(null) // null = pas sélectionné, true = dispo, false = pas simulé
const simulationLoaded = ref(false)

const tweets = ref([])
const events = ref([])
const currentIndex = ref(0)
const isPlaying = ref(false)
const speeds = [1, 5, 50]
const currentSpeed = ref(1)
const playInterval = ref(null)

const selectedTweet = ref(null)
const selectedTweetIndex = ref(null)
const activeEventId = ref(null)
const highlightedTweetIds = ref(new Set())

const trackRef = ref(null)
const mapRef = ref(null)
let leafletMap = null
let leafletMarkers = []

// ─── COMPUTED ─────────────────────────────────────────────────────────────────

const readHeadPercent = computed(() => {
  if (tweets.value.length <= 1) return 0
  return (currentIndex.value / (tweets.value.length - 1)) * 100
})

const visibleEvents = computed(() => {
  const processed = new Set(tweets.value.slice(0, currentIndex.value + 1).map(t => t.id))
  return events.value.filter(e => e.tweetIds.some(id => processed.has(id)))
})

const signalsDetected = computed(() =>
  tweets.value.slice(0, currentIndex.value + 1).filter(t => t.isSignal).length
)

const usefulLabeled = computed(() =>
  tweets.value.filter(t => t.label === true).length
)

const overlap = computed(() =>
  tweets.value.slice(0, currentIndex.value + 1).filter(t => t.isSignal && t.label === true).length
)

// ─── METHODS ──────────────────────────────────────────────────────────────────

function checkSimulation() {
  if (!selectedDataset.value || !selectedPipeline.value) {
    simulationStatus.value = null
    simulationLoaded.value = false
    return
  }
  const key = `${selectedDataset.value}-${selectedPipeline.value}`
  simulationStatus.value = simulatedPairs.value.has(key)
  if (simulationStatus.value) {
    loadSimulation()
  } else {
    simulationLoaded.value = false
  }
}

function loadSimulation() {
  // Replace with real API call: GET /simulations?dataset=X&pipeline=Y
  tweets.value = mockSimulationResult.tweets
  events.value = mockSimulationResult.events
  currentIndex.value = 0
  isPlaying.value = false
  selectedTweet.value = null
  activeEventId.value = null
  simulationLoaded.value = true
  nextTick(() => initMap())
}

function runSimulation() {
  // Replace with real API call: POST /simulations { dataset: X, pipeline: Y }
  const key = `${selectedDataset.value}-${selectedPipeline.value}`
  simulatedPairs.value.add(key)
  simulationStatus.value = true
  loadSimulation()
}

function togglePlay() {
  isPlaying.value = !isPlaying.value
}

function reset() {
  isPlaying.value = false
  currentIndex.value = 0
  selectedTweet.value = null
  activeEventId.value = null
  highlightedTweetIds.value = new Set()
  clearMapMarkers()
}

watch(isPlaying, (val) => {
  if (val) startPlayback()
  else stopPlayback()
})

watch(currentSpeed, () => {
  if (isPlaying.value) {
    stopPlayback()
    startPlayback()
  }
})

function startPlayback() {
  const baseInterval = 120
  playInterval.value = setInterval(() => {
    if (currentIndex.value < tweets.value.length - 1) {
      currentIndex.value++
      updateMapForIndex(currentIndex.value)
    } else {
      isPlaying.value = false
    }
  }, baseInterval / currentSpeed.value)
}

function stopPlayback() {
  clearInterval(playInterval.value)
}

function onTrackClick(e) {
  const rect = trackRef.value.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  currentIndex.value = Math.round(ratio * (tweets.value.length - 1))
  updateMapForIndex(currentIndex.value)
}

function selectTweet(tweet, idx) {
  selectedTweet.value = tweet
  selectedTweetIndex.value = idx
  activeEventId.value = null
  highlightedTweetIds.value = new Set()
}

function selectEvent(event) {
  activeEventId.value = event.id
  highlightedTweetIds.value = new Set(event.tweetIds)
  selectedTweet.value = null
}

function tweetDotClass(tweet, idx) {
  const isRead = idx <= currentIndex.value
  const isHighlighted = highlightedTweetIds.value.has(tweet.id)
  const isSelected = selectedTweet.value?.id === tweet.id

  let cls = ['tweet-dot']
  if (!isRead) cls.push('tweet-dot--future')
  else if (tweet.isSignal && tweet.label) cls.push('tweet-dot--both')
  else if (tweet.isSignal) cls.push('tweet-dot--signal')
  else if (tweet.label) cls.push('tweet-dot--useful')
  else cls.push('tweet-dot--none')

  if (isHighlighted) cls.push('tweet-dot--highlighted')
  if (isSelected) cls.push('tweet-dot--selected')
  return cls
}

function scoreColor(score) {
  if (score >= 0.7) return '#4ade80'
  if (score >= 0.4) return '#facc15'
  return '#f87171'
}

// ─── MAP ──────────────────────────────────────────────────────────────────────

function initMap() {
  if (leafletMap) {
    leafletMap.remove()
    leafletMap = null
  }
  if (!mapRef.value || typeof window === 'undefined') return

  // Dynamic Leaflet import
  import('leaflet').then(L => {
    leafletMap = L.default.map(mapRef.value, {
      center: [44.5, 16.0],
      zoom: 6,
      zoomControl: false,
      attributionControl: false,
    })

    L.default.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '©OpenStreetMap ©CartoDB',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(leafletMap)
  })
}

function updateMapForIndex(idx) {
  if (!leafletMap) return
  import('leaflet').then(L => {
    const processedIds = new Set(tweets.value.slice(0, idx + 1).map(t => t.id))
    const newEvents = events.value.filter(e =>
      e.tweetIds.some(id => processedIds.has(id)) &&
      !leafletMarkers.find(m => m._eventId === e.id)
    )
    newEvents.forEach(event => {
      const marker = L.default.circleMarker([event.lat, event.lng], {
        radius: 8,
        fillColor: '#ef4444',
        color: '#fca5a5',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      }).addTo(leafletMap)
      marker._eventId = event.id
      marker.bindTooltip(`<strong>${event.name}</strong><br>${event.location}`, { className: 'sim-tooltip' })
      leafletMarkers.push(marker)
    })
  })
}

function clearMapMarkers() {
  leafletMarkers.forEach(m => m.remove())
  leafletMarkers = []
}

onUnmounted(() => {
  stopPlayback()
  if (leafletMap) leafletMap.remove()
})
</script>

<style scoped>
/* ─── BASE ─────────────────────────────────────────────────────────────────── */
.simulation-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0d1117;
  color: #e6edf3;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  font-size: 13px;
  overflow: hidden;
}

/* ─── HEADER ────────────────────────────────────────────────────────────────── */
.sim-header {
  padding: 14px 24px 10px;
  border-bottom: 1px solid #21262d;
  background: #161b22;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.sim-header__selectors {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.selector-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
}

.sim-select {
  background: #21262d;
  color: #e6edf3;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 13px;
  outline: none;
  cursor: pointer;
  min-width: 220px;
  transition: border-color 0.15s;
}
.sim-select:hover { border-color: #58a6ff; }

.selector-sep {
  color: #30363d;
  font-size: 18px;
  margin-top: 14px;
}

.sim-status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  margin-top: 14px;
  border: 1px solid transparent;
}

.badge--ready {
  background: #0d2e1a;
  border-color: #238636;
  color: #3fb950;
}
.badge--missing {
  background: #2d1f00;
  border-color: #9e6a03;
  color: #e3b341;
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.badge--ready .badge-dot { background: #3fb950; box-shadow: 0 0 6px #3fb95066; }
.badge--missing .badge-dot { background: #e3b341; }

.btn-run {
  background: #e3b341;
  color: #0d1117;
  border: none;
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-run:hover { opacity: 0.85; }

.sim-header__counters {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #7d8590;
}
.counter strong { color: #e6edf3; }
.counter-sep { color: #30363d; }
.text-signal { color: #f87171; }
.text-useful { color: #facc15; }
.text-overlap { color: #4ade80; }

/* ─── BODY ───────────────────────────────────────────────────────────────────── */
.sim-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sim-col {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sim-col--left {
  width: 240px;
  min-width: 200px;
  border-right: 1px solid #21262d;
  background: #161b22;
}

.sim-col--center {
  flex: 1;
  padding: 20px;
  gap: 16px;
}

.sim-col--right {
  width: 280px;
  min-width: 240px;
  border-left: 1px solid #21262d;
  background: #161b22;
  overflow-y: auto;
}

/* ─── LEFT: Controls ────────────────────────────────────────────────────────── */
.controls-block {
  padding: 16px;
  border-bottom: 1px solid #21262d;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.controls-btns {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ctrl-btn {
  background: #21262d;
  border: 1px solid #30363d;
  color: #7d8590;
  width: 34px;
  height: 34px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.ctrl-btn:hover { border-color: #58a6ff; color: #58a6ff; }

.ctrl-btn--play {
  width: 40px;
  height: 40px;
  background: #1f6feb;
  border-color: #1f6feb;
  color: #fff;
  border-radius: 50%;
}
.ctrl-btn--play:hover { background: #388bfd; border-color: #388bfd; color: #fff; }

.speed-pills {
  display: flex;
  gap: 6px;
}
.speed-pill {
  background: #21262d;
  border: 1px solid #30363d;
  color: #7d8590;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}
.speed-pill.active {
  background: #1f6feb22;
  border-color: #1f6feb;
  color: #58a6ff;
}

/* ─── LEFT: Events ──────────────────────────────────────────────────────────── */
.events-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px;
}

.events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.events-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
}
.events-count {
  background: #21262d;
  border: 1px solid #30363d;
  color: #e6edf3;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
}

.events-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-card {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.event-card:hover { border-color: #58a6ff; }
.event-card--active {
  border-color: #f87171;
  background: #2d1f1f;
}
.event-card__name {
  font-size: 12px;
  font-weight: 500;
  color: #e6edf3;
  margin-bottom: 4px;
}
.event-card__meta {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #7d8590;
}
.events-empty {
  color: #7d8590;
  font-size: 12px;
  text-align: center;
  padding-top: 20px;
}

/* ─── CENTER: Timeline ──────────────────────────────────────────────────────── */
.timeline-block {
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 8px;
  padding: 16px;
  flex-shrink: 0;
}

.timeline-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
  margin-bottom: 16px;
}

.timeline-track {
  position: relative;
  height: 36px;
  background: #21262d;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 12px;
}

.timeline-readhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #58a6ff;
  border-radius: 1px;
  transition: left 0.1s linear;
  z-index: 2;
  box-shadow: 0 0 8px #58a6ff88;
}

.tweet-dot {
  position: absolute;
  top: 50%;
  transform: translateY(-50%) translateX(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.1s;
  z-index: 1;
}
.tweet-dot:hover { transform: translateY(-50%) translateX(-50%) scale(1.5); z-index: 3; }
.tweet-dot--future { background: #30363d; opacity: 0.4; }
.tweet-dot--none { background: #484f58; }
.tweet-dot--signal { background: #f87171; }
.tweet-dot--useful { border: 2px solid #facc15; background: transparent; }
.tweet-dot--both { background: #f87171; box-shadow: 0 0 0 2px #facc15; }
.tweet-dot--highlighted { box-shadow: 0 0 0 3px #58a6ff; z-index: 4; }
.tweet-dot--selected { box-shadow: 0 0 0 3px #fff; z-index: 5; }

.timeline-legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: #7d8590;
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-dot--signal { background: #f87171; }
.legend-dot--useful { border: 2px solid #facc15; background: transparent; }
.legend-dot--both { background: #f87171; box-shadow: 0 0 0 2px #facc15; }
.legend-dot--none { background: #484f58; }

/* ─── CENTER: Map ───────────────────────────────────────────────────────────── */
.map-block {
  flex: 1;
  position: relative;
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 8px;
  overflow: hidden;
  min-height: 200px;
}

#sim-map {
  width: 100%;
  height: 100%;
}

.map-label {
  position: absolute;
  bottom: 8px;
  left: 10px;
  font-size: 10px;
  color: #7d8590;
  background: #0d1117cc;
  padding: 2px 6px;
  border-radius: 4px;
  pointer-events: none;
}

/* ─── RIGHT: Detail ─────────────────────────────────────────────────────────── */
.detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #7d8590;
  text-align: center;
  gap: 10px;
  padding: 24px;
}
.detail-empty p { font-size: 12px; line-height: 1.5; }

.detail-panel {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-tweet-index {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
}

.detail-text {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  line-height: 1.5;
  color: #e6edf3;
}

.location-badge {
  display: inline-block;
  background: #1f3a5f;
  border: 1px solid #1f6feb;
  color: #58a6ff;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 12px;
}
.location-badge--none {
  background: #21262d;
  border-color: #30363d;
  color: #7d8590;
}

.detail-section-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7d8590;
}

.cascade {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cascade-step {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.cascade-step__left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 100px;
}
.cascade-index {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #21262d;
  border: 1px solid #30363d;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7d8590;
  flex-shrink: 0;
}
.cascade-model {
  font-size: 11px;
  color: #e6edf3;
}
.cascade-step__right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.cascade-bar {
  flex: 1;
  height: 4px;
  background: #21262d;
  border-radius: 2px;
  overflow: hidden;
}
.cascade-bar__fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s;
}
.cascade-score {
  font-size: 11px;
  font-weight: 600;
  min-width: 28px;
  text-align: right;
}
.cascade-verdict {
  font-size: 12px;
  min-width: 14px;
}
.cascade-verdict.pass { color: #4ade80; }
.cascade-verdict.fail { color: #f87171; }

.detail-verdict {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}
.verdict--signal { background: #2d1f1f; border: 1px solid #f87171; color: #f87171; }
.verdict--none { background: #1c1c1c; border: 1px solid #484f58; color: #7d8590; }

.detail-label {
  font-size: 12px;
  color: #7d8590;
  display: flex;
  gap: 6px;
  align-items: center;
}
.label-title { color: #7d8590; }
.label--useful { color: #4ade80; }
.label--notuseful { color: #f87171; }

/* ─── EMPTY STATE ────────────────────────────────────────────────────────────── */
.sim-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7d8590;
  font-size: 13px;
}

/* ─── SCROLLBAR ──────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }
</style>