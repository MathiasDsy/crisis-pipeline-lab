import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { pipelineService } from '@/services/pipelineService'
import type { PipelineConfig } from '@/types/pipeline'

export const usePipelineStore = defineStore('pipeline', () => {
  const pipelines   = ref<PipelineConfig[]>([])
  const isLoading   = ref(false)
  const isImporting = ref(false)
  const error       = ref<string | null>(null)
  const importError = ref<string | null>(null)
  const lastImportedId = ref<string | null>(null)

  // Per-pipeline transient state (id → busy flag)
  const validatingIds = ref<Set<string>>(new Set())
  const deletingIds   = ref<Set<string>>(new Set())

  const validCount   = computed(() => pipelines.value.filter((p) => p.is_valid).length)
  const invalidCount = computed(() => pipelines.value.filter((p) => !p.is_valid).length)

  // ── Read ────────────────────────────────────────────────
  async function load() {
    isLoading.value = true
    error.value = null
    try {
      pipelines.value = await pipelineService.list()
    } catch {
      error.value = 'Impossible de charger les pipelines'
    } finally {
      isLoading.value = false
    }
  }

  // ── Create ──────────────────────────────────────────────
  async function importFile(file: File) {
    isImporting.value = true
    importError.value = null
    lastImportedId.value = null
    try {
      const pl = await pipelineService.import(file)
      const idx = pipelines.value.findIndex((p) => p.id === pl.id)
      if (idx === -1) pipelines.value.unshift(pl)
      else pipelines.value[idx] = pl
      lastImportedId.value = pl.id
      return pl
    } catch (e) {
      importError.value = e instanceof Error ? e.message : 'Import échoué'
      throw e
    } finally {
      isImporting.value = false
    }
  }

  function clearImportError() {
    importError.value = null
  }

  // ── Validate ────────────────────────────────────────────
  async function validate(id: string) {
    validatingIds.value.add(id)
    try {
      const res = await pipelineService.validate(id)
      const pl = pipelines.value.find((p) => p.id === id)
      if (pl) {
        pl.is_valid = res.is_valid
        pl.validation_errors = res.errors
      }
      return res
    } catch {
      error.value = 'La validation a échoué'
    } finally {
      validatingIds.value.delete(id)
    }
  }

  // ── Delete ──────────────────────────────────────────────
  async function remove(id: string) {
    deletingIds.value.add(id)
    try {
      await pipelineService.delete(id)
      pipelines.value = pipelines.value.filter((p) => p.id !== id)
    } catch {
      error.value = 'La suppression a échoué'
    } finally {
      deletingIds.value.delete(id)
    }
  }

  return {
    pipelines,
    isLoading,
    isImporting,
    error,
    importError,
    lastImportedId,
    validatingIds,
    deletingIds,
    validCount,
    invalidCount,
    load,
    importFile,
    clearImportError,
    validate,
    remove,
  }
})
