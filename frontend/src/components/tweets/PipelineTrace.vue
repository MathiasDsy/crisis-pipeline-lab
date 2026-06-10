<template>
    <div class="trace-panel">
        <PipelineStepRow v-for="step in trace" :key="step.stepDbId" :step="step" @annotate-step="handleAnnotateStep" />
    </div>
</template>

<script setup lang="ts">
import PipelineStepRow from "./PipelineStepRow.vue"
import type { PipelineStep, AnnotationLabel } from "@/types/pipeline"

defineProps<{
    trace: PipelineStep[]
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