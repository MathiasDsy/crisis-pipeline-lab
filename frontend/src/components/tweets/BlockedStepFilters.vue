<template>
    <div class="blocked-step-filters">
        <button class="step-chip" :class="{ active: activeStep === null }" @click="$emit('update:active-step', null)">
            All blocked
            <span>{{ blockedRuns.length }}</span>
        </button>

        <button v-for="step in blockedSteps" :key="step.name" class="step-chip"
            :class="{ active: activeStep === step.name }" @click="$emit('update:active-step', step.name)">
            {{ formatStepName(step.name) }}
            <span>{{ step.count }}</span>
        </button>

    </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import type { PipelineRun } from "@/types/pipeline"

const props = defineProps<{
    runs: PipelineRun[]
    activeStep: string | null
}>()

defineEmits<{
    (e: "update:active-step", step: string | null): void
}>()

const blockedRuns = computed(() =>
    props.runs.filter(run => run.status === "blocked")
)

const blockedSteps = computed(() => {
    const counts = new Map<string, number>()

    for (const run of blockedRuns.value) {
        const step = "unknown"
        counts.set(step, (counts.get(step) || 0) + 1)
    }

    return [...counts.entries()]
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
})

function formatStepName(step: string) {
    return step
        .replaceAll("_", " ")
        .replace(/\b\w/g, char => char.toUpperCase())
}
</script>