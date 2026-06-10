<script setup lang="ts">
import GenericSidebar from '../components/shared/GenericSidebar.vue';
import { useEvents } from '../composables/useEvents.ts';
import type { FireEvent } from '@/types/events';

const {
    events,
    selectedEvent,
    eventSidebarItems,
    selectedEventId,
    loading,
    error,
    loadEvents,
    selectEvent
} = useEvents()



</script>

<template>
    <GenericSidebar title="Events" item-label="Event" :items="eventSidebarItems" :selected-item-id="selectedEventId"
        @select-item="(item) => selectEvent(item.id)"></GenericSidebar>

</template>