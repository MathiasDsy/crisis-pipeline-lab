<template>
    <div class="dashboard-view">
        <MapView class="map-area" />

        <RightPanel :events="events" :selected-event-id="selectedEventId" @select-event="selectedEventId = $event" />
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MapView from '../components/MapView.vue'
import TopBar from '../components/TopBar.vue'
import LeftNav from '../components/LeftNav.vue'
import RightPanel from '../components/RightPanel.vue'
import { getEvents } from '../services/api'
import type { CrisisEvent } from '../types/event'

const menuOpen = ref(false)


const events = ref<CrisisEvent[]>([])
const selectedEventId = ref<string | null>(null)

onMounted(async () => {
    events.value = await getEvents()
})

</script>

<style scoped>
.dashboard-view {
    width: 100%;
    height: 100%;

    display: flex;

    overflow: hidden;
}

.map-area {
    flex: 1;
    min-width: 0;
    height: 100%;

    overflow: hidden;
}
</style>