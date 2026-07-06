<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const isOpen = ref(false)
const route  = useRoute()

const navItems = [
  { name: 'Simulations', path: '/' },
  { name: 'Benchmark',   path: '/benchmark' },
  { name: 'Datasets',    path: '/datasets' },
  { name: 'Pipelines',   path: '/pipelines' },
  { name: 'Models',      path: '/models' },
]

function toggle() { isOpen.value = !isOpen.value }
function close()  { isOpen.value = false }
</script>

<template>
  <div class="nav-root">
    <!-- Burger button -->
    <button class="burger btn btn-ghost btn-icon" :class="{ active: isOpen }" @click="toggle" aria-label="Menu">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <Transition name="burger-icon" mode="out-in">
          <g v-if="!isOpen" key="open">
            <rect x="2" y="4"  width="12" height="1.5" rx="0.75" fill="currentColor"/>
            <rect x="2" y="7.25" width="12" height="1.5" rx="0.75" fill="currentColor"/>
            <rect x="2" y="10.5" width="12" height="1.5" rx="0.75" fill="currentColor"/>
          </g>
          <g v-else key="close">
            <line x1="3" y1="3" x2="13" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="13" y1="3" x2="3" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </g>
        </Transition>
      </svg>
    </button>

    <!-- Overlay -->
    <Transition name="fade">
      <div v-if="isOpen" class="nav-overlay" @click="close" />
    </Transition>

    <!-- Drawer -->
    <Transition name="slide-left">
      <nav v-if="isOpen" class="nav-drawer">
        <div class="nav-brand">
          <span class="nav-brand-text">Early Fire Detection</span>
        </div>

        <ul class="nav-list">
          <li v-for="item in navItems" :key="item.path">
            <RouterLink
              :to="item.path"
              class="nav-link"
              :class="{ 'nav-link--active': route.path === item.path }"
              @click="close"
            >
              {{ item.name }}
            </RouterLink>
          </li>
        </ul>

        <div class="nav-footer">
          <span class="text-xs text-muted">v1.0.0</span>
        </div>
      </nav>
    </Transition>
  </div>
</template>

<style scoped>
.nav-root {
  position: relative;
  z-index: 100;
}

.burger {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 200;
  color: var(--color-text-secondary);
}

.burger.active {
  color: var(--color-text-primary);
}

.nav-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.6);
  backdrop-filter: blur(2px);
  z-index: 150;
}

.nav-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--nav-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border-subtle);
  z-index: 160;
  display: flex;
  flex-direction: column;
  padding: var(--sp-4) 0;
}

.nav-brand {
  padding: var(--sp-2) var(--sp-5) var(--sp-5);
  border-bottom: 1px solid var(--color-border-subtle);
  margin-bottom: var(--sp-3);
}

.nav-brand-text {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.nav-list {
  list-style: none;
  padding: 0 var(--sp-2);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-link {
  display: block;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  transition: background var(--t-fast), color var(--t-fast);
  text-decoration: none;
}

.nav-link:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
}

.nav-link--active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.nav-footer {
  padding: var(--sp-4) var(--sp-5) 0;
  border-top: 1px solid var(--color-border-subtle);
  margin-top: var(--sp-3);
}

/* Burger icon transition */
.burger-icon-enter-active,
.burger-icon-leave-active { transition: opacity 100ms ease; }
.burger-icon-enter-from,
.burger-icon-leave-to     { opacity: 0; }
</style>
