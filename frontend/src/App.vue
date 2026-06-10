<template>
  <div class="app-layout">
    <TopBar :active-events="events.length" :alerts="1" @toggle-menu="menuOpen = true" @refresh="loadEvents"
      @run-simulation="runSimulation" />

    <LeftNav :open="menuOpen" @close="menuOpen = false" />

    <main class="app-body">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'

import TopBar from './components/TopBar.vue'
import LeftNav from './components/LeftNav.vue'

import { getEvents } from './services/api'
import type { CrisisEvent } from './types/event'

const menuOpen = ref(false)
const events = ref<CrisisEvent[]>([])

async function loadEvents() {
  events.value = await getEvents()
}

async function runSimulation() {
  console.log('Run simulation')
  // TODO: appeler ton endpoint de simulation ici
}

onMounted(() => {
  loadEvents()
})
</script>

<style scoped>
.app-layout {
  width: 100vw;
  height: 100vh;

  display: flex;
  flex-direction: column;

  overflow: hidden;

  background: #020617;
  color: #e2e8f0;
  font-family: Inter, system-ui, sans-serif;
}

.app-body {
  flex: 1;
  min-height: 0;
  width: 100%;

  overflow: hidden;
}
</style>