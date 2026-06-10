<script setup lang="ts">
import { computed, ref } from "vue";
import {
    mockBatches,
    mockConfigs,
    mockDatasets,
    mockHardCases,
    mockRuns,
} from "../mocks/benchmark.mock";

import LeftNav from "../components/LeftNav.vue";

const activeView = ref<"launch" | "results">("launch");
const menuOpen = ref(false);
const searchQuery = ref("");

const selectedDatasetIds = ref<string[]>(["ds_mixed_001"]);
const selectedConfigIds = ref<string[]>(["cfg_noise_hf_v1", "cfg_full_pipeline_v1"]);
const selectedBatchId = ref("batch_overnight_001");

const selectedBatch = computed(() =>
    mockBatches.find((batch) => batch.id === selectedBatchId.value)
);

const selectedRuns = computed(() =>
    mockRuns.filter((run) => run.batchId === selectedBatchId.value)
);

const totalPlannedRuns = computed(
    () => selectedDatasetIds.value.length * selectedConfigIds.value.length
);

const selectedTweetCount = computed(() =>
    mockDatasets
        .filter((dataset) => selectedDatasetIds.value.includes(dataset.id))
        .reduce((sum, dataset) => sum + dataset.tweetCount, 0)
);

function toggleDataset(datasetId: string) {
    selectedDatasetIds.value = selectedDatasetIds.value.includes(datasetId)
        ? selectedDatasetIds.value.filter((id) => id !== datasetId)
        : [...selectedDatasetIds.value, datasetId];
}

function toggleConfig(configId: string) {
    selectedConfigIds.value = selectedConfigIds.value.includes(configId)
        ? selectedConfigIds.value.filter((id) => id !== configId)
        : [...selectedConfigIds.value, configId];
}

function downloadDataset(dataset: { id: string; name: string; tweetCount: number; fileName: string }) {
    const csvContent = `id,name,tweetCount,fileName\n${dataset.id},${dataset.name},${dataset.tweetCount},${dataset.fileName}\n`;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const filename = dataset.fileName.endsWith(".csv")
        ? dataset.fileName
        : `${dataset.fileName}.csv`;

    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function launchBenchmark() {
    alert(
        `Launching benchmark with datasets: ${selectedDatasetIds.value.join(
            ", "
        )} and configs: ${selectedConfigIds.value.join(", ")}`
    );
}

</script>

<template>
    <div class="benchmark-page">
        <div class="left-side-panel">
            <div class="left-side-panel-header">
                <div>
                    <h2>Benchmark Lab</h2>

                    <LeftNav :open="menuOpen" @close="menuOpen = false" />

                    <p>Datasets, configs and runs.</p>
                </div>
                <span class="live-dot"></span>
            </div>
            <div class="search-box">
                <input v-model="searchQuery" type="text" placeholder="Search tweet, location, config..." />
            </div>

            <div class="left-side-panel-items"> <!-- Datasets, configs and runs sections -->

                <section class="sidebar-section">
                    <div class="section-title">
                        <span>Datasets</span>
                        <button class="ghost-btn">Import</button>
                    </div>

                    <div class="section-items">
                        <button v-for="dataset in mockDatasets" :key="dataset.id" class="sidebar-card"
                            :class="{ active: selectedDatasetIds.includes(dataset.id) }"
                            @click="toggleDataset(dataset.id)">
                            <strong>{{ dataset.name }}</strong>
                            <button class="ghost-btn" @click.stop="downloadDataset(dataset)">Download</button>
                            <small>{{ dataset.tweetCount }} tweets · {{ dataset.fileName }}</small>
                        </button>
                    </div>
                </section>

                <section class="sidebar-section">
                    <div class="section-title">
                        <span>YAML configs</span>
                        <button class="ghost-btn">Import</button>
                    </div>
                    <div class="section-items">
                        <button v-for="config in mockConfigs" :key="config.id" class="sidebar-card"
                            :class="{ active: selectedConfigIds.includes(config.id) }" @click="toggleConfig(config.id)">
                            <strong>{{ config.name }}</strong>
                            <small>{{ config.steps.length }} step(s) · {{ config.yamlFile }}</small>
                        </button>
                    </div>
                </section>

                <section class="sidebar-section">
                    <div class="section-title">
                        <span>Run history</span>
                    </div>
                    <div class="section-items">
                        <button v-for="batch in mockBatches" :key="batch.id" class="sidebar-card"
                            :class="{ active: selectedBatchId === batch.id }"
                            @click="selectedBatchId = batch.id; activeView = 'results'">
                            <strong>{{ batch.name }}</strong>
                            <small>{{ batch.status }} · {{ batch.configIds.length * batch.datasetIds.length }}
                                runs</small>
                        </button>
                    </div>
                </section>
            </div>
        </div>
        <main class="main-panel">
            <header class="main-header">
                <div>
                    <!-- <h1>Benchmark Batch Dashboard</h1> -->
                    <p>Launch computation-heavy evaluation batches and inspect hard cases.</p>
                </div>

                <div class="view-switcher">
                    <button :class="{ active: activeView === 'launch' }" @click="activeView = 'launch'">
                        Launch Batch
                    </button>
                    <button :class="{ active: activeView === 'results' }" @click="activeView = 'results'">
                        Explore Results
                    </button>
                </div>
            </header>

            <section v-if="activeView === 'launch'" class="content-grid">
                <div class="panel large-panel">
                    <h2>Batch setup</h2>
                    <p class="muted">
                        Select multiple datasets and configs. The backend will later expand this into
                        dataset × config benchmark runs.
                    </p>

                    <div class="setup-summary">
                        <div>
                            <span>Selected datasets</span>
                            <strong>{{ selectedDatasetIds.length }}</strong>
                        </div>
                        <div>
                            <span>Selected configs</span>
                            <strong>{{ selectedConfigIds.length }}</strong>
                        </div>
                        <div>
                            <span>Total runs</span>
                            <strong>{{ totalPlannedRuns }}</strong>
                        </div>
                        <div>
                            <span>Total tweets</span>
                            <strong>{{ selectedTweetCount }}</strong>
                        </div>
                    </div>

                    <button class="primary-action" @click="launchBenchmark">
                        Launch overnight benchmark
                    </button>
                </div>

                <div class="panel">
                    <h2>Selected configs</h2>

                    <div v-for="config in mockConfigs.filter((cfg) => selectedConfigIds.includes(cfg.id))"
                        :key="config.id" class="config-preview">
                        <strong>{{ config.name }}</strong>
                        <p>{{ config.description }}</p>
                        <small>{{config.steps.map((step) => step.name).join(" → ")}}</small>
                    </div>
                </div>
            </section>

            <section v-else class="results-layout">
                <div class="panel">
                    <h2>{{ selectedBatch?.name }}</h2>
                    <p class="muted">
                        {{ selectedRuns.length }} completed runs. Hard cases are ranked by lowest pass rate.
                    </p>

                    <div class="setup-summary">
                        <div>
                            <span>Runs</span>
                            <strong>{{ selectedRuns.length }}</strong>
                        </div>
                        <div>
                            <span>Best score</span>
                            <strong>{{Math.max(...selectedRuns.map((run) => run.globalScore))}}%</strong>
                        </div>
                        <div>
                            <span>Worst score</span>
                            <strong>{{Math.min(...selectedRuns.map((run) => run.globalScore))}}%</strong>
                        </div>
                    </div>
                </div>

                <div class="panel">
                    <h2>Runs</h2>

                    <table>
                        <thead>
                            <tr>
                                <th>Run</th>
                                <th>Dataset</th>
                                <th>Config</th>
                                <th>Score</th>
                                <th>Failed</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="run in selectedRuns" :key="run.id">
                                <td>{{ run.id }}</td>
                                <td>{{mockDatasets.find((d) => d.id === run.datasetId)?.name}}</td>
                                <td>{{mockConfigs.find((c) => c.id === run.configId)?.name}}</td>
                                <td>{{ run.globalScore }}%</td>
                                <td>{{ run.failedItems }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="panel">
                    <h2>Hard cases matrix</h2>

                    <table>
                        <thead>
                            <tr>
                                <th>Tweet</th>
                                <th>Pass rate</th>
                                <th>Failed runs</th>
                                <th>Main error</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="item in mockHardCases" :key="item.tweetId">
                                <td>
                                    <strong>{{ item.tweetId }}</strong>
                                    <p>{{ item.tweet }}</p>
                                </td>
                                <td>{{ item.passRate }}%</td>
                                <td>{{ item.failedRuns }}/{{ item.totalRuns }}</td>
                                <td>{{ item.mainErrorType }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </main>
    </div>
</template>


<style scoped>
/* ===== Global ===== */

.main-panel {
    padding: 32px;
    width: 75%;
    height: 100%;
    background: #07111f;
    color: #f5f7fa;
    font-family: Inter, sans-serif;
    overflow: auto;
}

.benchmark-page {
    display: flex;
    height: 100%;
    overflow: auto;
}

.left-side-panel {
    width: 25%;
    background: #050b16;
    border-right: 1px solid #1e293b;
    display: flex;
    flex-direction: column;
}

.left-side-panel-header {
    height: 56px;
    flex-shrink: 0;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 14px;

    border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.left-side-panel-header h2 {
    margin: 0;
    font-size: 14px;
    font-weight: 800;
    color: #f8fafc;
}

.left-side-panel-header p {
    margin: 3px 0 0;
    font-size: 11px;
    color: #64748b;
}

.live-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;

    background: #22c55e;
    box-shadow: 0 0 12px rgba(34, 197, 94, 0.6);
}

.search-box {
    flex-shrink: 0;
    padding: 10px 12px;

    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.search-box input {
    width: 100%;
    height: 34px;

    padding: 0 11px;

    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 10px;

    background: #020617;
    color: #e5e7eb;

    font-size: 12px;
    outline: none;
}

.search-box input::placeholder {
    color: #475569;
}

.search-box input:focus {
    border-color: rgba(59, 130, 246, 0.65);
}

.left-side-panel-items {
    flex-grow: 1;
    overflow-y: auto;
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.sidebar-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.section-items {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.sidebar-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    background: #0f1b2d;
    border: 1px solid #22324a;
    color: #cbd5e1;

    cursor: pointer;
    transition: background 0.15s ease;
}

.sidebar-card.active {
    background: #525e72;
    border-color: #2563eb;
    color: white;
}



/* ===== Header ===== */

.main-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;
    gap: 24px;
}

.main-header h1 {
    font-size: 2rem;
    margin-bottom: 8px;
    font-weight: 700;
}

.main-header p {
    color: #94a3b8;
    max-width: 600px;
    line-height: 1.5;
}

/* ===== Switch buttons ===== */

.view-switcher {
    display: flex;
    gap: 12px;
}

.view-switcher button {
    border: none;
    background: #132235;
    color: #cbd5e1;
    padding: 12px 18px;
    border-radius: 10px;
    cursor: pointer;
    transition: 0.2s ease;
    font-weight: 500;
}

.view-switcher button:hover {
    background: #1e314a;
}

.view-switcher button.active {
    background: #3b82f6;
    color: white;
}

/* ===== Layout ===== */

.content-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    align-items: start;
}

/* ===== Panels ===== */

.panel {
    background: #0f1b2d;
    border: 1px solid #1e293b;
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}

.large-panel {
    min-height: 320px;
}

.panel h2 {
    font-size: 1.4rem;
    margin-bottom: 12px;
}

.muted {
    color: #94a3b8;
    line-height: 1.5;
    margin-bottom: 24px;
}

/* ===== Summary cards ===== */

.setup-summary {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}

.setup-summary div {
    background: #132235;
    border-radius: 14px;
    padding: 18px;
    border: 1px solid #22324a;
}

.setup-summary span {
    display: block;
    color: #94a3b8;
    font-size: 0.9rem;
    margin-bottom: 8px;
}

.setup-summary strong {
    font-size: 1.8rem;
    font-weight: 700;
    color: white;
}

/* ===== Main action ===== */

.primary-action {
    border: none;
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    color: white;
    padding: 14px 22px;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s ease;
}

.primary-action:hover {
    opacity: 0.95;
}

/* ===== Config preview ===== */

.config-preview {
    background: #132235;
    border: 1px solid #22324a;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
}

.config-preview strong {
    display: block;
    margin-bottom: 8px;
    font-size: 1rem;
}

.config-preview p {
    color: #cbd5e1;
    line-height: 1.4;
    margin-bottom: 10px;
}

.config-preview small {
    color: #64748b;
    font-size: 0.8rem;
}

/* ===== Responsive ===== */

@media (max-width: 1000px) {
    .content-grid {
        grid-template-columns: 1fr;
    }

    .main-header {
        flex-direction: column;
    }

    .setup-summary {
        grid-template-columns: 1fr;
    }
}

/* ===== Results layout ===== */

.results-layout {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* ===== Tables ===== */

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 18px;
    border-radius: 14px;
    background: #132235;
}

thead {
    background: #1e293b;
}

th {
    text-align: left;
    padding: 16px;
    font-size: 0.9rem;
    color: #94a3b8;
    font-weight: 600;
    border-bottom: 1px solid #334155;
}

td {
    padding: 16px;
    border-bottom: 1px solid #22324a;
    vertical-align: top;
    color: #f1f5f9;
}

tbody tr {
    transition: background 0.15s ease;
}

tbody tr:hover {
    background: rgba(59, 130, 246, 0.08);
}

/* ===== Tweet cell ===== */

td p {
    margin-top: 6px;
    color: #94a3b8;
    line-height: 1.4;
    max-width: 700px;
}

/* ===== Score styling ===== */

.score-good {
    color: #22c55e;
    font-weight: 700;
}

.score-medium {
    color: #facc15;
    font-weight: 700;
}

.score-bad {
    color: #ef4444;
    font-weight: 700;
}

/* ===== Hard cases ===== */

.panel table tr td:first-child {
    min-width: 320px;
}

/* ===== Panel spacing ===== */

.results-layout .panel {
    overflow-x: auto;
}

/* ===== Sticky table header (optional but nice) ===== */

thead th {
    position: sticky;
    top: 0;
    z-index: 2;
}

/* ===== Responsive ===== */

@media (max-width: 900px) {

    table {
        font-size: 0.9rem;
    }

    th,
    td {
        padding: 12px;
    }

    .panel table tr td:first-child {
        min-width: 220px;
    }
}
</style>
