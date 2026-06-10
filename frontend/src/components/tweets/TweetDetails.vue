<template>
    <main v-if="selectedRun" class="details-panel">
        <section class="detail-header">
            <div>
                <span class="eyebrow">Selected tweet</span>
                <h1>{{ selectedRun.text }}</h1>
            </div>

            <span class="summary-badge" :class="selectedRun.status">
                {{ selectedRun.status }}
            </span>
        </section>

        <PipelineTrace :trace="selectedRun.trace" @annotate-step="handleAnnotateStep" />
    </main>

    <main v-else class="details-panel empty-details">
        Select a tweet.
    </main>
</template>

<script setup lang="ts">
import PipelineTrace from "./PipelineTrace.vue"
import type { PipelineRun } from "@/types/pipeline"
import type { AnnotationLabel } from "@/types/pipeline"

defineProps<{
    selectedRun: PipelineRun | null
}>()

const emit = defineEmits<{
    annotateStep: [
        payload: {
            pipelineStepId: string
            label: AnnotationLabel
        }
    ]
}>()

function handleAnnotateStep(payload: {
    pipelineStepId: string
    label: AnnotationLabel
}) {
    emit("annotateStep", payload)
}
</script>