<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Tweet, StepExecution } from '@/types/tweet'

const props = defineProps<{
  tweets: Tweet[]
  trace:  StepExecution[]
}>()

type TweetFilter = 'all' | 'passed' | 'blocked' | 'error'
const activeFilter = ref<TweetFilter>('all')
const expandedId   = ref<string | null>(null)

/* Group trace by tweet_id */
const traceByTweet = computed(() => {
  const map = new Map<string, StepExecution[]>()
  for (const step of props.trace) {
    const list = map.get(step.tweet_id) ?? []
    list.push(step)
    map.set(step.tweet_id, list)
  }
  return map
})

type TweetStatus = 'passed' | 'blocked' | 'error'

interface EnrichedTweet {
  tweet:      Tweet
  steps:      StepExecution[]
  status:     TweetStatus
  blockedAt?: string
}

const enriched = computed<EnrichedTweet[]>(() =>
  props.tweets.map((tweet) => {
    const steps = (traceByTweet.value.get(tweet.id) ?? []).sort(
      (a, b) => a.step_index - b.step_index,
    )

    const errorStep   = steps.find((s) => s.status === 'error')
    const blockedStep = steps.find((s) => s.status === 'blocked')

    if (errorStep)   return { tweet, steps, status: 'error',   blockedAt: errorStep.step_name }
    if (blockedStep) return { tweet, steps, status: 'blocked', blockedAt: blockedStep.step_name }
    return { tweet, steps, status: 'passed' }
  }),
)

/* Funnel stats */
const funnel = computed(() => {
  const stepNames = [...new Set(props.trace.map((s) => s.step_name))].sort(
    (a, b) => {
      const ai = props.trace.find((s) => s.step_name === a)?.step_index ?? 0
      const bi = props.trace.find((s) => s.step_name === b)?.step_index ?? 0
      return ai - bi
    },
  )

  return stepNames.map((name) => {
    const steps = props.trace.filter((s) => s.step_name === name)
    return {
      name,
      total:   steps.length,
      passed:  steps.filter((s) => s.status === 'success').length,
      blocked: steps.filter((s) => s.status === 'blocked').length,
      error:   steps.filter((s) => s.status === 'error').length,
    }
  })
})

const filtered = computed(() => {
  if (activeFilter.value === 'all') return enriched.value
  return enriched.value.filter((e) => e.status === activeFilter.value)
})

const counts = computed(() => ({
  all:     enriched.value.length,
  passed:  enriched.value.filter((e) => e.status === 'passed').length,
  blocked: enriched.value.filter((e) => e.status === 'blocked').length,
  error:   enriched.value.filter((e) => e.status === 'error').length,
}))

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}

function stepStatusClass(status: string) {
  return status === 'success' ? 'step-success'
       : status === 'blocked' ? 'step-blocked'
       : 'step-error'
}

function formatMs(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`
}
</script>

<template>
  <div class="tweet-list">
    <!-- Funnel -->
    <div v-if="funnel.length > 0" class="funnel">
      <div class="section-label funnel-title">Pipeline funnel</div>
      <div class="funnel-steps">
        <div class="funnel-start">
          <span class="funnel-count">{{ tweets.length }}</span>
          <span class="text-xs text-muted">tweets</span>
        </div>

        <template v-for="step in funnel" :key="step.name">
          <div class="funnel-arrow">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v12M4 10l4 4 4-4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="funnel-step">
            <div class="funnel-step-name">{{ step.name }}</div>
            <div class="funnel-step-stats">
              <span class="stat-pass">{{ step.passed }} pass</span>
              <span v-if="step.blocked > 0" class="stat-block">{{ step.blocked }} blocked</span>
              <span v-if="step.error > 0"   class="stat-err">{{ step.error }} err</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="filter-bar">
      <button
        v-for="(count, key) in counts"
        :key="key"
        class="filter-tab"
        :class="{ 'filter-tab--active': activeFilter === key }"
        @click="activeFilter = key as TweetFilter"
      >
        {{ key.charAt(0).toUpperCase() + key.slice(1) }}
        <span class="filter-count">{{ count }}</span>
      </button>
    </div>

    <!-- Empty -->
    <div v-if="filtered.length === 0" class="empty-state">
      <p class="text-sm text-muted">No tweets match this filter.</p>
    </div>

    <!-- Tweet rows -->
    <ul v-else class="tweet-items">
      <li
        v-for="item in filtered"
        :key="item.tweet.id"
        class="tweet-row"
        :class="`tweet-row--${item.status}`"
      >
        <div class="tweet-row-header" @click="toggleExpand(item.tweet.id)">
          <!-- Status dot -->
          <span class="tweet-dot" :class="`tweet-dot--${item.status}`" />

          <!-- Content -->
          <span class="tweet-text truncate">{{ item.tweet.content }}</span>

          <!-- Right info -->
          <div class="tweet-meta">
            <span v-if="item.blockedAt" class="blocked-at text-xs">
              blocked @ {{ item.blockedAt }}
            </span>
            <span v-else-if="item.status === 'passed'" class="passed-label text-xs">
              passed
            </span>
            <svg
              class="expand-icon"
              :class="{ expanded: expandedId === item.tweet.id }"
              width="12" height="12" viewBox="0 0 12 12" fill="none"
            >
              <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </div>
        </div>

        <!-- Expanded trace -->
        <Transition name="slide-up">
          <div v-if="expandedId === item.tweet.id" class="tweet-trace">
            <div
              v-for="step in item.steps"
              :key="step.id"
              class="trace-step"
              :class="stepStatusClass(step.status)"
            >
              <div class="trace-step-header">
                <span class="trace-step-name">{{ step.step_name }}</span>
                <span class="trace-step-status">{{ step.status }}</span>
                <span class="trace-step-duration text-muted">{{ formatMs(step.duration_ms) }}</span>
              </div>
              <div v-if="Object.keys(step.output_json).length" class="trace-output font-mono text-xs">
                {{ JSON.stringify(step.output_json, null, 2) }}
              </div>
            </div>
          </div>
        </Transition>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.tweet-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
}

/* ── Funnel ──────────────────────────────────────────────── */
.funnel {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
}

.funnel-title {
  margin-bottom: var(--sp-4);
}

.funnel-steps {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
}

.funnel-start {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  padding: var(--sp-2) 0;
}

.funnel-count {
  font-size: var(--text-xl);
  font-weight: var(--fw-semibold);
  color: var(--color-text-primary);
}

.funnel-arrow {
  color: var(--color-text-muted);
  padding: var(--sp-1) 0;
  margin-left: 4px;
}

.funnel-step {
  padding: var(--sp-2) var(--sp-3);
  background: var(--color-surface-elevated);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  width: 100%;
}

.funnel-step-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text-secondary);
  min-width: 160px;
}

.funnel-step-stats {
  display: flex;
  gap: var(--sp-3);
  font-size: var(--text-xs);
}

.stat-pass  { color: var(--color-success); }
.stat-block { color: var(--color-warning); }
.stat-err   { color: var(--color-error); }

/* ── Filter bar ──────────────────────────────────────────── */
.filter-bar {
  display: flex;
  gap: var(--sp-1);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--sp-3);
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-1) var(--sp-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast);
}

.filter-tab:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
}

.filter-tab--active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.filter-count {
  font-size: var(--text-xs);
  background: var(--color-surface-elevated);
  padding: 1px 6px;
  border-radius: 999px;
}

/* ── Tweet rows ──────────────────────────────────────────── */
.tweet-items {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tweet-row {
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid transparent;
  transition: border-color var(--t-fast);
}

.tweet-row:hover {
  border-color: var(--color-border);
}

.tweet-row-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  cursor: pointer;
}

.tweet-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tweet-dot--passed  { background: var(--color-success); }
.tweet-dot--blocked { background: var(--color-warning); }
.tweet-dot--error   { background: var(--color-error); }

.tweet-text {
  flex: 1;
  font-size: var(--text-sm);
  min-width: 0;
}

.tweet-meta {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-shrink: 0;
}

.blocked-at { color: var(--color-warning); }
.passed-label { color: var(--color-success); }

.expand-icon {
  color: var(--color-text-muted);
  transition: transform var(--t-fast);
  flex-shrink: 0;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

/* ── Trace ───────────────────────────────────────────────── */
.tweet-trace {
  border-top: 1px solid var(--color-border-subtle);
  padding: var(--sp-3);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  background: var(--color-surface);
}

.trace-step {
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  border-left: 2px solid transparent;
}

.step-success { border-color: var(--color-success);  background: var(--color-success-subtle); }
.step-blocked { border-color: var(--color-warning);  background: var(--color-warning-subtle); }
.step-error   { border-color: var(--color-error);    background: var(--color-error-subtle); }

.trace-step-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-1);
}

.trace-step-name   { font-size: var(--text-sm); font-weight: var(--fw-medium); }
.trace-step-status { font-size: var(--text-xs); color: var(--color-text-secondary); }
.trace-step-duration { font-size: var(--text-xs); margin-left: auto; }

.trace-output {
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--color-text-secondary);
  line-height: 1.6;
  max-height: 160px;
  overflow-y: auto;
}
</style>
