<template>
    <div class="filter-tabs">
        <button v-for="tab in tabs" :key="tab.key" class="filter-tab" :class="{ active: activeTab === tab.key }"
            @click="$emit('update:activeTab', tab.key)">
            <span>{{ tab.label }}</span>
            <strong>{{ tab.count }}</strong>
        </button>
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import type { PipelineRun, TabKey } from "@/types/pipeline"

const props = defineProps<{
    runs: PipelineRun[]
    activeTab: TabKey
}>()

defineEmits<{
    "update:activeTab": [tab: TabKey]
}>()

const tabs = computed(() => [
    { key: "recent" as const, label: "Recent", count: props.runs.length },
    { key: "passed" as const, label: "Passed", count: props.runs.filter(r => r.status === "passed").length },
    { key: "warning" as const, label: "Warning", count: props.runs.filter(r => r.status === "warning").length },
    { key: "blocked" as const, label: "Blocked", count: props.runs.filter(r => r.status === "blocked").length },
])
</script>