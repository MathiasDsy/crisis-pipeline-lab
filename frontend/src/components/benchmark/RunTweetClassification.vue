<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ClassifiedTweet, ClassKind } from '@/types/tweet'

const props = defineProps<{
  tweets:    ClassifiedTweet[]
  isLoading: boolean
}>()

type Filter = 'all' | ClassKind
const activeFilter = ref<Filter>('all')

const counts = computed(() => ({
  all: props.tweets.length,
  TP:  props.tweets.filter((t) => t.kind === 'TP').length,
  FP:  props.tweets.filter((t) => t.kind === 'FP').length,
  FN:  props.tweets.filter((t) => t.kind === 'FN').length,
  TN:  props.tweets.filter((t) => t.kind === 'TN').length,
}))

const filtered = computed(() =>
  activeFilter.value === 'all'
    ? props.tweets
    : props.tweets.filter((t) => t.kind === activeFilter.value),
)

const tabs: { key: Filter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'TP',  label: 'True Positive' },
  { key: 'FP',  label: 'False Positive' },
  { key: 'FN',  label: 'False Negative' },
  { key: 'TN',  label: 'True Negative' },
]

function kindClass(kind: ClassKind | null) {
  return kind ? `kind-${kind.toLowerCase()}` : 'kind-na'
}
</script>

<template>
  <div class="tweet-classification">
    <div class="tc-header">
      <span class="text-sm font-medium">Tweets</span>
      <span class="text-xs text-muted">{{ tweets.length }} classified</span>
    </div>

    <!-- Filter tabs -->
    <div class="tc-filters">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tc-tab"
        :class="[{ 'tc-tab--active': activeFilter === tab.key }, tab.key !== 'all' ? `tc-tab--${tab.key.toLowerCase()}` : '']"
        @click="activeFilter = tab.key"
      >
        {{ tab.label }}
        <span class="tc-count">{{ counts[tab.key] }}</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="tc-loading">
      <span class="spinner" />
      <span class="text-sm text-muted">Loading tweets…</span>
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0" class="tc-empty">
      <span class="text-sm text-muted">No tweets for this filter.</span>
    </div>

    <!-- List -->
    <ul v-else class="tc-list">
      <li v-for="t in filtered" :key="t.tweet_id" class="tc-row">
        <span class="tc-badge" :class="kindClass(t.kind)">{{ t.kind ?? '—' }}</span>
        <span class="tc-text">{{ t.text || '(no text)' }}</span>
        <span v-if="t.label !== null" class="tc-flags text-xs text-muted">
          label={{ t.label ? '1' : '0' }} · pred={{ t.predicted ? '1' : '0' }}
        </span>
        <span v-else class="tc-flags text-xs text-muted">unlabeled</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.tweet-classification {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.tc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ── Filters ─────────────────────────────────────────────── */
.tc-filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--sp-3);
}

.tc-tab {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-1) var(--sp-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--t-fast), color var(--t-fast), border-color var(--t-fast);
}

.tc-tab:hover {
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
}

.tc-tab--active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  border-color: rgba(59, 130, 246, 0.25);
}

.tc-count {
  font-size: var(--text-xs);
  background: var(--color-surface-elevated);
  padding: 1px 6px;
  border-radius: 999px;
}

/* ── Rows ────────────────────────────────────────────────── */
.tc-loading,
.tc-empty {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4);
  color: var(--color-text-muted);
}

.tc-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 420px;
  overflow-y: auto;
}

.tc-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
}

.tc-row:hover { background: var(--color-surface-elevated); }

.tc-badge {
  flex-shrink: 0;
  width: 30px;
  text-align: center;
  font-size: 10px;
  font-weight: var(--fw-semibold);
  padding: 2px 0;
  border-radius: var(--radius-sm);
}

.kind-tp { background: var(--color-success-subtle); color: var(--color-success); }
.kind-fp { background: var(--color-error-subtle);   color: var(--color-error); }
.kind-fn { background: var(--color-warning-subtle); color: var(--color-warning); }
.kind-tn { background: var(--color-surface-elevated); color: var(--color-text-muted); }
.kind-na { background: var(--color-surface-elevated); color: var(--color-text-muted); }

.tc-text {
  flex: 1;
  min-width: 0;
  font-size: var(--text-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tc-flags { flex-shrink: 0; }
</style>
