<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import type { FireEvent } from '@/types/event'

const props = defineProps<{
  events: FireEvent[]
}>()

const mapEl  = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markers: L.Layer[] = []

function initMap() {
  if (!mapEl.value) return
  map = L.map(mapEl.value, {
    center: [44.5, 16.5],
    zoom: 7,
    zoomControl: true,
  })

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © CARTO',
    maxZoom: 18,
  }).addTo(map)
}

function renderEvents() {
  if (!map) return

  markers.forEach((m) => m.remove())
  markers = []

  if (props.events.length === 0) return

  const bounds: [number, number][] = []

  props.events.forEach((ev) => {
    const circle = L.circle([ev.center_lat, ev.center_lon], {
      radius: ev.radius_km * 1000,
      color:  ev.is_active ? '#ef4444' : '#64748b',
      fillColor: ev.is_active ? '#ef4444' : '#64748b',
      fillOpacity: 0.15,
      weight: 2,
    })
      .bindPopup(
        `<div style="font-family:inherit;font-size:13px;color:#e2e8f0;background:#1e293b;padding:8px 10px;border-radius:6px;min-width:200px">
          <div style="font-weight:600;margin-bottom:4px">${ev.is_active ? 'Active event' : 'Closed event'}</div>
          <div style="color:#94a3b8;margin-bottom:6px">${ev.tweet_count} tweet${ev.tweet_count !== 1 ? 's' : ''} · r=${ev.radius_km} km</div>
          <div style="color:#cbd5e1;font-size:12px">${ev.latest_tweet_text ?? ''}</div>
        </div>`,
        { className: 'map-popup' },
      )
      .addTo(map!)

    markers.push(circle)
    bounds.push([ev.center_lat, ev.center_lon])
  })

  if (bounds.length > 0) {
    map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 12 })
  }
}

watch(() => props.events, renderEvents, { deep: true })

onMounted(() => {
  initMap()
  renderEvents()
})

onUnmounted(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div class="run-map">
    <div v-if="events.length === 0" class="map-empty">
      <span class="text-sm text-muted">No geo events for this run</span>
    </div>
    <div ref="mapEl" class="map-container" />
  </div>
</template>

<style scoped>
.run-map {
  position: relative;
  height: 380px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border-subtle);
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  z-index: 10;
}
</style>
