<template>
    <aside class="nav" :class="{ open }">
        <div class="nav-header">
            <span class="title">Navigation</span>
            <button class="close" @click="$emit('close')">✕</button>
        </div>

        <div class="nav-body">
            <nav class="nav-links">
                <RouterLink to="/" class="nav-link" exact-active-class="active">
                    Dashboard
                </RouterLink>

                <RouterLink to="/events" class="nav-link" exact-active-class="active">
                    Events
                </RouterLink>

                <RouterLink to="/tweets" class="nav-link" exact-active-class="active">
                    Tweets
                </RouterLink>

                <RouterLink to="/pipeline" class="nav-link" exact-active-class="active">
                    Pipeline
                </RouterLink>

                <RouterLink to="/benchmarks" class="nav-link" exact-active-class="active">
                    Benchmark
                </RouterLink>




                <!-- <RouterLink to="/logs" class="nav-link" exact-active-class="active">
                    Logs
                </RouterLink>

                <RouterLink to="/models" class="nav-link" exact-active-class="active">
                    Models
                </RouterLink>

                <RouterLink to="/config" class="nav-link" exact-active-class="active">
                    Config
                </RouterLink>

                <RouterLink to="/simulation" class="nav-link" exact-active-class="active">
                    Simulation
                </RouterLink> -->
            </nav>

            <div class="nav-footer">
                <div class="footer-title">Crisis Monitor</div>
                <div class="footer-subtitle">Operational Wildfire Detection System</div>
                <div class="footer-meta">v0.1 • Split-Dalmatia Region</div>
                <div class="footer-meta muted">Powered by OSM, Photon, FastAPI</div>
            </div>
        </div>
    </aside>

    <div v-if="open" class="backdrop" @click="$emit('close')"></div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
    open: boolean
}>()

defineEmits<{
    (e: 'close'): void
}>()
</script>

<style scoped>
.nav {
    position: absolute;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    z-index: 1200;
    display: flex;
    flex-direction: column;
    padding: 18px;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    background: rgba(10, 14, 22, 0.96);
    backdrop-filter: blur(18px);
    color: white;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.nav.open {
    transform: translateX(0);
}

.nav-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
}

.title {
    font-size: 15px;
    font-weight: 700;
}

.close {
    width: 34px;
    height: 34px;
    border: none;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08);
    color: white;
    cursor: pointer;
}

.nav-body {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
}

.nav-links {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.nav-link {
    display: block;
    padding: 12px 14px;
    border-radius: 12px;
    color: rgba(255, 255, 255, 0.78);
    text-decoration: none;
    font-size: 14px;
    transition: 0.2s ease;
}

.nav-link:hover {
    background: rgba(255, 255, 255, 0.06);
    color: white;
}

.nav-link.active {
    background: rgba(59, 130, 246, 0.18);
    color: #93c5fd;
}

.backdrop {
    position: absolute;
    inset: 0;
    z-index: 1100;
    background: rgba(0, 0, 0, 0.28);
}

.nav-footer {
    margin-top: 24px;
    padding-top: 18px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.footer-title {
    font-size: 13px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.92);
}

.footer-subtitle {
    margin-top: 4px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.62);
    line-height: 1.4;
}

.footer-meta {
    margin-top: 10px;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.48);
}

.footer-meta.muted {
    margin-top: 4px;
}
</style>