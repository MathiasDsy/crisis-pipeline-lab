<template>
    <aside class="tweets-panel">
        <div class="panel-header">
            <div>
                <h2>Tweet Logs</h2>
                <p>{{ runs.length }} processed tweets</p>
            </div>
            <span class="live-dot"></span>
        </div>

        <div class="search-box">
            <input v-model="searchQuery" type="text" placeholder="Search tweet, location, config..." />
        </div>

        <TweetFilterTabs v-model:active-tab="activeTab" :runs="runs" @tab-change="handleTabChange" />

        <BlockedStepFilters v-if="activeTab === 'blocked'" v-model:active-step="activeBlockedStep" :runs="runs" />

        <div class="panel-actions">
            <button class="export-btn">Export dataset</button>
            <button class="ghost-btn">Refresh</button>
        </div>

        <div class="tweets-list">
            <TweetRow v-for="run in filteredRuns" :key="run.id" :run="run" :selected="selectedRun === run.id"
                @click="handleClick(run)" />
        </div>
    </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue"
import TweetFilterTabs from "./TweetFilterTabs.vue"
import BlockedStepFilters from "./BlockedStepFilters.vue"
import TweetRow from "./TweetRow.vue"
import type { PipelineRun, TabKey } from "@/types/pipeline"

const props = defineProps<{
    runs: PipelineRun[]
    selectedRun: string | null
}>()

const emit = defineEmits<{
    (e: "select-tweet", tweetId: string): void
}>()

const activeTab = ref<TabKey>("recent")
const activeBlockedStep = ref<string | null>(null)
const searchQuery = ref("")

function handleClick(run: PipelineRun) {
    emit("select-tweet", run.id)
}

function handleTabChange(tab: TabKey) {
    if (tab !== "blocked") {
        activeBlockedStep.value = null
    }
}

const filteredRuns = computed(() => {
    const query = searchQuery.value.toLowerCase().trim()

    return props.runs.filter(run => {
        const matchTab =
            activeTab.value === "recent" || run.status === activeTab.value

        const matchBlockedStep =
            activeTab.value !== "blocked" ||
            !activeBlockedStep.value ||
            run.blocked_at === activeBlockedStep.value

        const matchSearch =
            !query ||
            run.text?.toLowerCase().includes(query) ||
            run.config?.toLowerCase().includes(query) ||
            run.status?.toLowerCase().includes(query) ||
            run.blocked_at?.toLowerCase().includes(query)

        return matchTab && matchBlockedStep && matchSearch
    })
})
</script>