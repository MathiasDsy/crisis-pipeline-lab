import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { modelService } from '@/services/modelService'
import type { HfImportBody } from '@/services/modelService'
import type { Model } from '@/types/model'
import type { HfModel } from '@/types/huggingface'

export type ModelTab = 'classifier' | 'ner'

interface TabConfig {
  model_type:            string
  loader:                string
  compatible_components: string[]
  component_key:         string
}

const TAB_CONFIG: Record<ModelTab, TabConfig> = {
  classifier: {
    model_type:            'classifier',
    loader:                'transformers',
    compatible_components: ['relevance_classifier'],
    component_key:         'relevance_classifier',
  },
  ner: {
    model_type:            'location_extractor',
    loader:                'gliner',
    compatible_components: ['location_extractor'],
    component_key:         'location_extractor',
  },
}

function toModelKey(repoId: string): string {
  return repoId.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
}

export const useModelStore = defineStore('model', () => {
  // ── Installed models ────────────────────────────────────
  const installed     = ref<Model[]>([])
  const isLoading     = ref(false)
  const isDiscovering = ref(false)
  const error         = ref<string | null>(null)

  // ── HuggingFace browser ─────────────────────────────────
  const activeTab   = ref<ModelTab>('classifier')
  const query       = ref('')
  const results     = ref<HfModel[]>([])
  const isSearching = ref(false)
  const searchError = ref<string | null>(null)
  const hasSearched = ref(false)

  // repo_ids currently downloading
  const importingRepos = ref<Set<string>>(new Set())
  const importError    = ref<string | null>(null)

  // ZIP upload
  const isUploadingZip = ref(false)
  const zipError       = ref<string | null>(null)

  // Max-parameter budget filter (in millions). MAX = no limit.
  const MAX_PARAMS_M = 2000
  const maxParamsM   = ref(MAX_PARAMS_M)

  // ── Computed ────────────────────────────────────────────
  const installedByTab = computed(() => {
    const key = TAB_CONFIG[activeTab.value].component_key
    return installed.value.filter((m) => m.compatible_components_key.includes(key))
  })

  const installedRepoIds = computed(() => {
    const set = new Set<string>()
    for (const m of installed.value) {
      const repo = (m.metadata_json?.repo_id ?? m.metadata_json?.name) as string | undefined
      if (repo) set.add(repo)
      set.add(m.model_key)
    }
    return set
  })

  function isInstalled(hf: HfModel): boolean {
    return installedRepoIds.value.has(hf.repo_id) || installedRepoIds.value.has(toModelKey(hf.repo_id))
  }

  const paramLimitReached = computed(() => maxParamsM.value >= MAX_PARAMS_M)

  // Filter results by the param budget. Models with unknown size are always kept.
  const filteredResults = computed(() => {
    if (paramLimitReached.value) return results.value
    const maxParams = maxParamsM.value * 1_000_000
    return results.value.filter(
      (m) => m.num_parameters === null || m.num_parameters <= maxParams,
    )
  })

  // ── Actions ─────────────────────────────────────────────
  async function loadInstalled() {
    isLoading.value = true
    error.value = null
    try {
      installed.value = await modelService.list()
    } catch {
      error.value = 'Impossible de charger les modèles'
    } finally {
      isLoading.value = false
    }
  }

  async function discover() {
    isDiscovering.value = true
    try {
      await modelService.discover()
      await loadInstalled()
    } catch {
      error.value = 'Le scan des modèles a échoué'
    } finally {
      isDiscovering.value = false
    }
  }

  function setTab(tab: ModelTab) {
    activeTab.value = tab
  }

  async function search() {
    const q = query.value.trim()
    if (!q) return
    isSearching.value = true
    searchError.value = null
    hasSearched.value = true
    try {
      const res = await modelService.searchHuggingface(q)
      results.value = res.models
    } catch (e) {
      searchError.value = e instanceof Error ? e.message : 'Recherche échouée'
      results.value = []
    } finally {
      isSearching.value = false
    }
  }

  async function importModel(hf: HfModel) {
    const cfg = TAB_CONFIG[activeTab.value]
    importingRepos.value.add(hf.repo_id)
    importError.value = null
    try {
      const body: HfImportBody = {
        repo_id:               hf.repo_id,
        model_key:             toModelKey(hf.repo_id),
        model_type:            cfg.model_type,
        loader:                cfg.loader,
        compatible_components: cfg.compatible_components,
        version:               '1.0.0',
      }
      await modelService.importHuggingface(body)
      await loadInstalled()
    } catch (e) {
      importError.value = e instanceof Error ? e.message : 'Import échoué'
    } finally {
      importingRepos.value.delete(hf.repo_id)
    }
  }

  async function importZip(file: File) {
    isUploadingZip.value = true
    zipError.value = null
    try {
      await modelService.importUpload(file)
      await loadInstalled()
    } catch (e) {
      zipError.value = e instanceof Error ? e.message : 'Import échoué'
    } finally {
      isUploadingZip.value = false
    }
  }

  function clearZipError() {
    zipError.value = null
  }

  return {
    installed,
    isLoading,
    isDiscovering,
    isUploadingZip,
    zipError,
    error,
    activeTab,
    query,
    results,
    isSearching,
    searchError,
    hasSearched,
    importingRepos,
    importError,
    maxParamsM,
    MAX_PARAMS_M,
    paramLimitReached,
    filteredResults,
    installedByTab,
    isInstalled,
    loadInstalled,
    discover,
    importZip,
    clearZipError,
    setTab,
    search,
    importModel,
  }
})
