<script setup lang="ts">
import { ref } from 'vue'
import type { Dataset } from '@/types/dataset'
import type { PipelineConfig } from '@/types/pipeline'

const props = defineProps<{
  datasets:    Dataset[]
  pipelines:   PipelineConfig[]
  isStarting:  boolean
}>()

const emit = defineEmits<{
  submit: [payload: { datasetId: string; pipelineId: string; forceRerun: boolean }]
  cancel: []
}>()

const selectedDatasetId  = ref('')
const selectedPipelineId = ref('')
const forceRerun         = ref(false)

const isValid = () => selectedDatasetId.value !== '' && selectedPipelineId.value !== ''

function submit() {
  if (!isValid() || props.isStarting) return
  emit('submit', {
    datasetId:  selectedDatasetId.value,
    pipelineId: selectedPipelineId.value,
    forceRerun: forceRerun.value,
  })
}
</script>

<template>
  <div class="new-run-form card">
    <div class="form-header">
      <h3 class="form-title">New simulation</h3>
      <button class="btn btn-ghost btn-icon btn-sm" @click="emit('cancel')">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <div class="form-body">
      <div class="form-group">
        <label class="form-label">Dataset</label>
        <select v-model="selectedDatasetId" class="form-select">
          <option value="" disabled>Select a dataset…</option>
          <option
            v-for="ds in datasets"
            :key="ds.id"
            :value="ds.id"
            :disabled="!ds.is_valid"
          >
            {{ ds.name }}
            <template v-if="!ds.is_valid"> (invalid)</template>
          </option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Pipeline</label>
        <select v-model="selectedPipelineId" class="form-select">
          <option value="" disabled>Select a pipeline…</option>
          <option
            v-for="pl in pipelines"
            :key="pl.id"
            :value="pl.id"
            :disabled="!pl.is_valid"
          >
            {{ pl.name }} {{ pl.version }}
            <template v-if="!pl.is_valid"> (invalid)</template>
          </option>
        </select>
      </div>

      <label class="checkbox-label">
        <input v-model="forceRerun" type="checkbox" class="checkbox-input" />
        <span class="text-sm text-secondary">Force rerun (ignore cache)</span>
      </label>
    </div>

    <div class="form-footer">
      <button class="btn btn-ghost" @click="emit('cancel')">Cancel</button>
      <button
        class="btn btn-primary"
        :disabled="!isValid() || isStarting"
        @click="submit"
      >
        <span v-if="isStarting" class="spinner" />
        {{ isStarting ? 'Starting…' : 'Run simulation' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.new-run-form {
  border-color: var(--color-border);
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-5);
}

.form-title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  margin-bottom: var(--sp-5);
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  accent-color: var(--color-accent);
  width: 14px;
  height: 14px;
  cursor: pointer;
}
</style>
