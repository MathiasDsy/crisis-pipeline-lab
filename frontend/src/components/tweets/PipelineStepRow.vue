<template>
    <div class="step-row" :class="step.status">
        <div class="step-marker">
            {{ stepIcon(step.status) }}
        </div>

        <div class="step-content">
            <div class="step-head">
                <h3>{{ step.name }}</h3>
                <span>{{ step.duration }} ms</span>
            </div>

            <p>{{ step.description }}</p>

            <pre>{{ JSON.stringify(step.output, null, 2) }}</pre>

            <div class="step-annotation">
                <button v-for="option in annotationOptions" :key="option.label" class="annotation-button" :class="[
                    option.label,
                    { active: currentAnnotation === option.label }
                ]" :title="option.title" @click="annotate(option.label)">
                    {{ option.icon }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import type { PipelineStep, StepStatus } from "@/types/pipeline"

type AnnotationLabel = "correct" | "incorrect" | "uncertain"

const props = defineProps<{
    step: PipelineStep
}>()

const emit = defineEmits<{
    annotateStep: [
        payload: {
            pipelineStepId: string
            label: AnnotationLabel
        }
    ]
}>()

const annotationOptions: {
    label: AnnotationLabel
    icon: string
    title: string
}[] = [
        { label: "correct", icon: "✓", title: "Correct" },
        { label: "incorrect", icon: "✕", title: "Incorrect" },
        { label: "uncertain", icon: "!", title: "Uncertain" },
    ]

const currentAnnotation = computed(() => {
    return props.step.annotation?.label ?? null
})

function annotate(label: AnnotationLabel) {
    if (!props.step.stepDbId) return

    emit("annotateStep", {
        pipelineStepId: props.step.stepDbId,
        label,
    })
}

function stepIcon(status: StepStatus) {
    if (status === "success") return "✓"
    if (status === "failed") return "✕"
    if (status === "warning") return "!"
    return "✕"
}
</script>

<style scoped>
.step-annotation {
    display: flex;
    gap: 0.4rem;
    margin-top: 0.75rem;
}

.annotation-button {
    width: 28px;
    height: 28px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    background: rgba(255, 255, 255, 0.04);
    color: inherit;
    cursor: pointer;
    opacity: 0.45;
}


.annotation-button.active {
    opacity: 1;
    border-color: currentColor;
    background: rgba(255, 255, 255, 0.12);
    font-weight: 700;
}

.annotation-button:hover {
    opacity: 0.85;
    transform: scale(1.05) ease;
}

/* ========================================= */
/* CORRECT */
/* ========================================= */

.annotation-button.correct {
    background: rgba(34, 197, 94, 0.12);
    color: rgb(134, 239, 172);
}

.annotation-button.correct.active {
    background: rgba(34, 197, 94, 0.22);
    border-color: rgba(134, 239, 172, 0.7);
    opacity: 1;
}

/* ========================================= */
/* INCORRECT */
/* ========================================= */

.annotation-button.incorrect {
    background: rgba(239, 68, 68, 0.12);
    color: rgb(252, 165, 165);
}

.annotation-button.incorrect.active {
    background: rgba(239, 68, 68, 0.22);
    border-color: rgba(252, 165, 165, 0.7);
    opacity: 1;
}

/* ========================================= */
/* UNCERTAIN */
/* ========================================= */

.annotation-button.uncertain {
    background: rgba(234, 179, 8, 0.12);
    color: rgb(253, 224, 71);
}

.annotation-button.uncertain.active {
    background: rgba(234, 179, 8, 0.22);
    border-color: rgba(253, 224, 71, 0.7);
    opacity: 1;
}
</style>