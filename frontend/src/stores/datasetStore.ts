import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { datasetService } from '@/services/datasetService'
import type { Dataset, DatasetPreview } from '@/types/dataset'

export const useDatasetStore = defineStore('dataset', () => {
  const datasets    = ref<Dataset[]>([])
  const isLoading   = ref(false)
  const isDiscovering = ref(false)
  const isImporting = ref(false)
  const error       = ref<string | null>(null)
  const importError = ref<string | null>(null)
  const lastImportedId = ref<string | null>(null)

  // ── Preview state ───────────────────────────────────────
  const previewId      = ref<string | null>(null)
  const preview        = ref<DatasetPreview | null>(null)
  const isLoadingPreview = ref(false)

  // ── Computed ────────────────────────────────────────────
  const validCount   = computed(() => datasets.value.filter((d) => d.is_valid).length)
  const invalidCount = computed(() => datasets.value.filter((d) => !d.is_valid).length)

  // ── Actions ─────────────────────────────────────────────
  async function load() {
    isLoading.value = true
    error.value = null
    try {
      datasets.value = await datasetService.list()
    } catch {
      error.value = 'Impossible de charger les datasets'
    } finally {
      isLoading.value = false
    }
  }

  async function discover() {
    isDiscovering.value = true
    error.value = null
    try {
      datasets.value = await datasetService.discover()
    } catch {
      error.value = 'Le scan des datasets a échoué'
    } finally {
      isDiscovering.value = false
    }
  }

  async function importCsv(file: File) {
    isImporting.value  = true
    importError.value  = null
    lastImportedId.value = null
    try {
      const ds = await datasetService.import(file)
      // Upsert into the list (import overwrites a same-name file server-side).
      const idx = datasets.value.findIndex((d) => d.path === ds.path)
      if (idx === -1) datasets.value.unshift(ds)
      else datasets.value[idx] = ds
      lastImportedId.value = ds.id
      return ds
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

  async function openPreview(id: string) {
    if (previewId.value === id) {
      closePreview()
      return
    }
    previewId.value = id
    preview.value   = null
    isLoadingPreview.value = true
    try {
      preview.value = await datasetService.preview(id)
    } catch {
      error.value = 'Aperçu indisponible pour ce dataset'
      previewId.value = null
    } finally {
      isLoadingPreview.value = false
    }
  }

  function closePreview() {
    previewId.value = null
    preview.value   = null
  }

  return {
    datasets,
    isLoading,
    isDiscovering,
    isImporting,
    error,
    importError,
    lastImportedId,
    previewId,
    preview,
    isLoadingPreview,
    validCount,
    invalidCount,
    load,
    discover,
    importCsv,
    clearImportError,
    openPreview,
    closePreview,
  }
})
