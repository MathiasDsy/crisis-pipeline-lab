import { onMounted, computed, ref, onUnmounted } from "vue" 
import type { FireEvent } from "@/types/event"
import { fetchAllEvents } from "../api/eventsApi"
import type { SidebarItem } from "@/types/sidebar"


export function useEvents() {

    const events = ref<FireEvent[]>([])
    const selectedEventId = ref<string | null>(null)
    const loading = ref(false)
    const error = ref<string | null>(null)

    let intervalId: number | null = null

    const selectedEvent = computed(() => {
        return events.value.find(e => e.id == selectedEventId.value) ?? null
    })

    async function loadEvents(silent = false) {
        if (!silent) loading.value = true
        error.value = null

        try {
            events.value = await fetchAllEvents()
            
            if (events.value.length > 0 && !selectedEventId.value) {
                selectedEventId.value = events.value[0].id
            }
        } catch (err: any) {
            error.value = err.message ?? "Unknown error"
        } finally {
            if (!silent) loading.value = false
        }
    }

    function selectEvent(eventId: string) {
        selectedEventId.value = eventId 
    }

    onMounted(() => {
        loadEvents()

        intervalId = window.setInterval(() => {
            loadEvents(true)
        }, 3000)
    })

    onUnmounted(() => {
        if (intervalId !== null) {
            clearInterval(intervalId)
        }
    })

    const eventSidebarItems = computed<SidebarItem[]>(() =>
        events.value.map(event => ({
            id: event.id,
            title: `${event.center_lat}, ${event.center_lon}` || "Unknown location",
            subtitle: `${event.center_lat}, ${event.center_lon}` || "Unknown location",
            description: `${event.tweet_count} tweets · confidence ${Math.round(event.confidence * 100)}%`,

            status: event.status,
            statusLabel: event.status.toUpperCase(),

            searchText: [
            `${event.center_lat}, ${event.center_lon}`,
            event.status,
            event.id
            ].filter(Boolean).join(" ").toLowerCase(),

            meta: [
            { label: "Tweets", value: event.tweet_count },
            { label: "Confidence", value: `${Math.round(event.confidence * 100)}%` }
            ],

            raw: event
        }))
    )

    return {
        events,
        selectedEvent,
        eventSidebarItems,
        selectedEventId,
        loading,
        error,
        loadEvents,
        selectEvent
    }
}