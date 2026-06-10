<script setup lang="ts">
import { useTweets } from "../composables/useTweets.ts"
import TweetsSidebar from "../components/tweets/TweetsSidebar.vue"
import TweetDetails from "../components/tweets/TweetDetails.vue"
import "../assets/tweet.css"
import type { AnnotationLabel } from "@/types/pipeline"
import { annotatePipelineStep } from "../api/tweetsApi.ts"

const {
    tweets,
    selectedTweet,
    selectedTweetId,
    loading,
    error,
    loadTweets,
    selectTweet,
} = useTweets()

async function handleAnnotateStep(payload: {
    pipelineStepId: string
    label: AnnotationLabel
}) {
    // 1. Update local immédiat
    updateStepAnnotationLocal(payload.pipelineStepId, payload.label)

    // 2. Persist DB
    await annotatePipelineStep(payload)
}

function updateStepAnnotationLocal(
    pipelineStepId: string,
    label: AnnotationLabel
) {
    const tweet = tweets.value.find(t =>
        t.trace.some(step => step.stepDbId === pipelineStepId)
    )

    if (!tweet) return

    const step = tweet.trace.find(step => step.stepDbId === pipelineStepId)

    if (!step) return

    step.annotation = {
        id: step.annotation?.id ?? "local-temp",
        label,
        annotatedBy: "mathias",
        notes: step.annotation?.notes ?? null,
        annotatedAt: new Date().toISOString(),
    }
}



</script>

<template>
    <div class="tweets-page">
        <div v-if="loading">Loading tweets...</div>
        <div v-else-if="error">
            {{ error }}
            <button @click="loadTweets">Retry</button>
        </div>

        <template v-else>
            <TweetsSidebar :runs="tweets" :selected-run="selectedTweetId" @select-tweet="selectTweet" />

            <TweetDetails :selected-run="selectedTweet" @annotate-step="handleAnnotateStep" />
        </template>
    </div>
</template>