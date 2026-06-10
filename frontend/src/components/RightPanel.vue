<template>
    <aside class="right-panel">
        <section class="panel-section">
            <div class="section-header">
                <h2>Active Events</h2>
                <span class="count">{{ events.length }}</span>
            </div>

            <div class="event-list">
                <button v-for="event in events" :key="event.id" class="event-card"
                    @click="$emit('select-event', event.id)">
                    <div class="event-top">
                        <span class="severity-dot"></span>
                        <strong>{{ event.status }}</strong>
                        <span class="tweet-count">{{ event.tweet_count }} reports</span>
                    </div>

                    <p class="event-text">
                        {{ event.latest_tweet_text || 'No report available' }}
                    </p>

                    <div class="event-meta">
                        <span>{{ event.center_lat.toFixed(3) }}, {{ event.center_lon.toFixed(3) }}</span>
                        <span>{{ formatDate(event.updated_at) }}</span>
                    </div>
                </button>
            </div>
        </section>

        <section class="panel-section">
            <div class="section-header">
                <h2>Warnings</h2>
                <span class="count warning">1</span>
            </div>

            <div class="warning-card">
                <strong>Wind data missing</strong>
                <p>No weather snapshot attached to active events yet.</p>
            </div>
        </section>

        <section class="panel-section">
            <div class="section-header">
                <h2>Selected Incident</h2>
            </div>

            <div v-if="selectedEvent" class="incident-card">
                <h3>🔥 Event {{ selectedEvent.id.slice(0, 8) }}</h3>
                <p>{{ selectedEvent.latest_tweet_text || 'No latest tweet' }}</p>

                <div class="incident-grid">
                    <span>Status</span>
                    <strong>{{ selectedEvent.status }}</strong>

                    <span>Radius</span>
                    <strong>{{ selectedEvent.radius_km }} km</strong>

                    <span>Reports</span>
                    <strong>{{ selectedEvent.tweet_count }}</strong>

                    <span>Finished</span>
                    <strong>{{ selectedEvent.is_finished ? 'Yes' : 'No' }}</strong>
                </div>
            </div>

            <div v-else class="empty-state">
                Select an event on the map or in the list.
            </div>
        </section>
    </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CrisisEvent } from '../types/event'

const props = defineProps<{
    events: CrisisEvent[]
    selectedEventId: string | null
}>()

defineEmits<{
    (e: 'select-event', id: string): void
}>()

const selectedEvent = computed(() =>
    props.events.find(e => e.id === props.selectedEventId) ?? null
)

function formatDate(value: string) {
    return new Date(value).toLocaleTimeString()
}
</script>

<style scoped>
.right-panel {
    width: 360px;
    height: 100%;
    flex-shrink: 0;

    display: flex;
    flex-direction: column;
    gap: 14px;

    padding: 14px;

    background: rgba(12, 16, 24, 0.96);
    color: white;

    border-left: 1px solid rgba(255, 255, 255, 0.08);

    overflow-y: auto;
}

.panel-section {
    padding: 14px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.045);
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

h2 {
    margin: 0;
    font-size: 14px;
    font-weight: 700;
}

.count {
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 12px;
    background: rgba(239, 68, 68, 0.18);
    color: #fca5a5;
}

.count.warning {
    background: rgba(245, 158, 11, 0.18);
    color: #fcd34d;
}

.event-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.event-card {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 14px;

    background: rgba(255, 255, 255, 0.06);
    color: white;
    text-align: left;
    cursor: pointer;
}

.event-card:hover {
    background: rgba(255, 255, 255, 0.1);
}

.event-top {
    display: flex;
    align-items: center;
    gap: 8px;
}

.severity-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #ef4444;
}

.tweet-count {
    margin-left: auto;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.55);
}

.event-text {
    margin: 8px 0;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.76);
    line-height: 1.35;
}

.event-meta {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.45);
}

.warning-card {
    padding: 12px;
    border-radius: 14px;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.22);
}

.warning-card strong {
    font-size: 13px;
    color: #fcd34d;
}

.warning-card p {
    margin: 6px 0 0;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.68);
}

.incident-card h3 {
    margin: 0 0 8px;
    font-size: 15px;
}

.incident-card p {
    margin: 0 0 12px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.72);
}

.incident-grid {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
    font-size: 12px;
}

.incident-grid span {
    color: rgba(255, 255, 255, 0.5);
}

.empty-state {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.55);
}
</style>