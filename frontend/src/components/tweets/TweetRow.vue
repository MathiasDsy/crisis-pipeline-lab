<template>
    <button class="tweet-row" :class="[run.status, { selected }]">
        <div class="row-top">
            <span class="status-pill">{{ run.status }}</span>
            <!-- <span class="status-pill" v-if="run.status === 'blocked'">@</span> -->
            <span class="time">{{ formatDate(run.createdAt) }}</span>
        </div>

        <p class="tweet-text">{{ run.text }}</p>

        <div class="row-meta">
            <span>{{ run.config }}</span>
            <span>{{ "completed" }}</span>
        </div>
    </button>
</template>



<script setup lang="ts">
import type { PipelineRun } from "@/types/pipeline"

const props = defineProps<{
    run: PipelineRun
    selected: boolean
}>()

const formatDate = (date: string) => {
    return new Date(date).toLocaleString("fr-FR", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    })
}
</script>