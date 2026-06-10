<template>
    <header class="topbar">
        <button class="burger" @click="$emit('toggle-menu')">
            ☰
        </button>

        <div class="brand">
            <span class="logo">🔥</span>
            <div>
                <h1>Crisis Monitor</h1>
                <p>Split-Dalmatia wildfire detection</p>
            </div>
        </div>
        <div class="actions">
            <button class="action-btn" @click="$emit('refresh')">
                Refresh
            </button>

            <button class="action-btn primary" @click="$emit('run-simulation')">
                Run Simulation
            </button>

            <select class="time-select">
                <option>Last hour</option>
                <option>Last 6 hours</option>
                <option>Today</option>
            </select>
        </div>

        <div class="status">
            <div class="status-item">
                <span class="dot active"></span>
                <span>{{ activeEvents }} active events</span>
            </div>

            <div class="status-item">
                <span class="dot warning"></span>
                <span>{{ alerts }} alerts</span>
            </div>

            <div class="system-status" title="System online">
                <span class="pulse-dot"></span>
            </div>
        </div>
    </header>
</template>

<script setup lang="ts">
defineProps<{
    activeEvents: number
    alerts: number
}>()

defineEmits<{
    (e: 'toggle-menu'): void
    (e: 'refresh'): void
    (e: 'run-simulation'): void
}>()
</script>

<style scoped>
.topbar {
    height: 64px;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding-inline: 12px;

    background: #0b1220;
    color: white;

    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.burger {
    width: 42px;
    height: 42px;
    border: none;
    border-radius: 12px;

    background: rgba(255, 255, 255, 0.08);
    color: white;
    font-size: 22px;
    cursor: pointer;
}

.burger:hover {
    background: rgba(255, 255, 255, 0.16);
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-right: auto;
    margin-left: 16px;
}

.logo {
    font-size: 26px;
}

h1 {
    margin: 0;
    font-size: 17px;
    font-weight: 700;
}

p {
    margin: 2px 0 0;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.62);
}

.status {
    display: flex;
    align-items: center;
    gap: 18px;
    font-size: 13px;
}

.status-item {
    display: flex;
    align-items: center;
    gap: 7px;
    color: rgba(255, 255, 255, 0.84);
}

.dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
}

.dot.active {
    background: #ef4444;
}

.dot.warning {
    background: #f59e0b;
}

.system-ok {
    padding: 7px 10px;
    border-radius: 999px;
    background: rgba(34, 197, 94, 0.15);
    color: #86efac;
    font-size: 12px;
}

.actions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
    margin-right: 18px;
}

.action-btn {
    height: 34px;
    padding: 0 12px;
    border: none;
    border-radius: 10px;

    background: rgba(255, 255, 255, 0.08);
    color: white;

    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
}

.action-btn:hover {
    background: rgba(255, 255, 255, 0.15);
}

.action-btn.primary {
    background: rgba(239, 68, 68, 0.2);
    color: #fecaca;
}

.action-btn.primary:hover {
    background: rgba(239, 68, 68, 0.32);
}

.time-select {
    height: 34px;
    padding: 0 10px;
    border: none;
    border-radius: 10px;

    background: rgba(255, 255, 255, 0.08);
    color: white;

    font-size: 12px;
    cursor: pointer;
}

.system-status {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
}

.pulse-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #22c55e;
    animation: pulse 1.8s infinite ease-in-out;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.35);
}

@keyframes pulse {
    0% {
        transform: scale(0.9);
        opacity: 0.7;
    }

    50% {
        transform: scale(1.35);
        opacity: 1;
    }

    100% {
        transform: scale(0.9);
        opacity: 0.7;
    }
}
</style>