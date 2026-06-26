<template>
    <div id="map"></div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import L from 'leaflet'
import { getEvents } from '../services/api'

let map: L.Map
let eventLayer: L.LayerGroup

onMounted(async () => {
    map = L.map('map').setView([43.5081, 16.4402], 9)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map)

    eventLayer = L.layerGroup().addTo(map)

    await loadEvents()
})

function flyToPoint(lat: number, lon: number, zoom: number = 12) {
    console.log(`Fly to point: ${lat}, ${lon} with zoom ${zoom}`)
    map?.flyTo([lat, lon], zoom)
}


async function loadEvents() {
    const events = await getEvents()
    
    eventLayer.clearLayers()
    
    for (const event of events) {
        const lat = event.center_lat
        const lon = event.center_lon
        
        L.marker([lat, lon])
        .addTo(eventLayer)
        .bindPopup(`
        <strong>🔥 Event</strong><br/>
        ID: ${event.id}<br/>
        Status: ${event.status}<br/>
        Tweets: ${event.tweet_count}<br/>
        Latest: ${event.latest_tweet_text ?? 'No tweet'}<br/>
        Radius: ${event.radius_km} km
        `)
        
        L.circle([lat, lon], {
            radius: event.radius_km * 1000
        }).addTo(eventLayer)
    }
}
defineExpose({
  flyToPoint
})
</script>

<style scoped>
#map {
    width: 100%;
    height: 100%;
}
</style>