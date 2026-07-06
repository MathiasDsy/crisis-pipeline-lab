<script setup lang="ts">
import type { RunStatus } from '@/types/run'

const props = defineProps<{
  status: RunStatus
}>()

const labelMap: Record<RunStatus, string> = {
  running:   'Running',
  completed: 'Completed',
  cancelled: 'Cancelled',
  error:     'Error',
}

const classMap: Record<RunStatus, string> = {
  running:   'badge-running',
  completed: 'badge-success',
  cancelled: 'badge-cancelled',
  error:     'badge-error',
}
</script>

<template>
  <span class="badge" :class="classMap[props.status]">
    <span v-if="props.status === 'running'" class="spinner" />
    {{ labelMap[props.status] }}
  </span>
</template>
