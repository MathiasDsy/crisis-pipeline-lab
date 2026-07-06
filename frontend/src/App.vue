<script setup lang="ts">
import AppNav from '@/components/AppNav.vue'
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-layout">
    <AppNav />
    <main class="app-body">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
}

.app-body {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
</style>
