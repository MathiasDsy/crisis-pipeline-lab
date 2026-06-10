<template>
    <aside class="tweets-panel">
        <div class="panel-header">
            <div>
                <h2>{{ title }}</h2>
                <p>{{ items.length }} {{ itemLabel }}</p>
            </div>
            <span v-if="live" class="live-dot"></span>
        </div>

        <div class="search-box">
            <input v-model="searchQuery" type="text" :placeholder="searchPlaceholder" />
        </div>

        <div class="filter-tabs">
            <button v-for="tab in computedTabs" :key="tab.key" :class="{ active: activeTab === tab.key }"
                @click="setActiveTab(tab.key)">
                {{ tab.label }}
                <span>{{ countByTab(tab.key) }}</span>
            </button>
        </div>

        <div v-if="activeTab === 'blocked' && blockedSteps.length" class="blocked-distribution">
            <button class="step-chip" :class="{ active: activeBlockedStep === null }" @click="activeBlockedStep = null">
                All blocked
                <span>{{ blockedItems.length }}</span>
            </button>

            <button v-for="step in blockedSteps" :key="step.name" class="step-chip"
                :class="{ active: activeBlockedStep === step.name }" @click="activeBlockedStep = step.name">
                {{ formatLabel(step.name) }}
                <span>{{ step.count }}</span>
            </button>
        </div>

        <div class="panel-actions">
            <button v-for="action in actions" :key="action.label"
                :class="action.variant === 'ghost' ? 'ghost-btn' : 'export-btn'" @click="action.onClick?.()">
                {{ action.label }}
            </button>
        </div>

        <div class="tweets-list">
            <div v-for="item in filteredItems" :key="item.id" class="tweet-row"
                :class="{ selected: selectedItemId === item.id }" @click="$emit('select-item', item)">
                <div class="tweet-row-header">
                    <span class="status-pill" :class="item.status">
                        {{ item.statusLabel || formatLabel(item.status) }}
                    </span>

                    <span v-if="item.badges?.length" class="row-badges">
                        <span v-for="badge in item.badges" :key="badge.label" class="mini-badge"
                            :class="badge.type || 'neutral'">
                            {{ badge.label }}
                        </span>
                    </span>
                </div>

                <h3>{{ item.title }}</h3>

                <p v-if="item.subtitle" class="row-subtitle">
                    {{ item.subtitle }}
                </p>

                <p v-if="item.description" class="row-description">
                    {{ item.description }}
                </p>

                <div v-if="item.meta?.length" class="event-meta">
                    <span v-for="meta in item.meta" :key="meta.label">
                        {{ meta.label }}: {{ meta.value }}
                    </span>
                </div>
            </div>
        </div>
    </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue"
import type { SidebarItem, SidebarTab } from "@/types/sidebar"

const props = withDefaults(defineProps<{
    title: string
    itemLabel: string
    items: SidebarItem[]
    selectedItemId: string | null
    tabs?: SidebarTab[]
    live?: boolean
    searchPlaceholder?: string
    actions?: {
        label: string
        variant?: "primary" | "ghost"
        onClick?: () => void
    }[]
}>(), {
    live: false,
    searchPlaceholder: "Search...",
    actions: () => []
})

defineEmits<{
    (e: "select-item", item: SidebarItem): void
}>()

const searchQuery = ref("")
const activeTab = ref("all")
const activeBlockedStep = ref<string | null>(null)

const computedTabs = computed(() => {
    if (props.tabs?.length) return props.tabs

    const statuses = [...new Set(props.items.map(item => item.status))]

    return [
        { key: "all", label: "All" },
        ...statuses.map(status => ({
            key: status,
            label: formatLabel(status)
        }))
    ]
})

const blockedItems = computed(() =>
    props.items.filter(item => item.status === "blocked")
)

const blockedSteps = computed(() => {
    const counts = new Map<string, number>()

    for (const item of blockedItems.value) {
        if (!item.blockedAt) continue
        counts.set(item.blockedAt, (counts.get(item.blockedAt) || 0) + 1)
    }

    return [...counts.entries()]
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
})

const filteredItems = computed(() => {
    const query = searchQuery.value.toLowerCase().trim()

    return props.items.filter(item => {
        const matchTab =
            activeTab.value === "all" ||
            item.status === activeTab.value

        const matchBlockedStep =
            activeTab.value !== "blocked" ||
            !activeBlockedStep.value ||
            item.blockedAt === activeBlockedStep.value

        const matchSearch =
            !query ||
            item.searchText.toLowerCase().includes(query)

        return matchTab && matchBlockedStep && matchSearch
    })
})

function countByTab(tabKey: string) {
    if (tabKey === "all") return props.items.length
    return props.items.filter(item => item.status === tabKey).length
}

function setActiveTab(tab: string) {
    activeTab.value = tab

    if (tab !== "blocked") {
        activeBlockedStep.value = null
    }
}

function formatLabel(value: string) {
    return value
        .replaceAll("_", " ")
        .replace(/\b\w/g, char => char.toUpperCase())
}
</script>