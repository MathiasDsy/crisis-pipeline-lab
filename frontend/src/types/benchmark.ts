export type BenchmarkStatus = "pending" | "running" | "completed" | "failed";
export type BenchmarkRunType = "evaluation" | "training";

export interface Dataset {
  id: string;
  name: string;
  type: "noise_only" | "candidates_only" | "mixed" | "custom";
  fileName: string;
  tweetCount: number;
  labelsSummary: Record<string, number>;
  createdAt: string;
}

export interface BenchmarkStep {
  id: string;
  name: string;
  type: "noise_filter" | "location_extraction" | "source_judge" | "event_clustering" | "custom";
  model?: string;
  provider?: "huggingface" | "local" | "openai" | "custom";
  metrics: string[];
}

export interface BenchmarkConfig {
  id: string;
  name: string;
  description: string;
  yamlFile: string;
  steps: BenchmarkStep[];
  createdAt: string;
}

export interface BenchmarkBatch {
  id: string;
  name: string;
  runType: BenchmarkRunType;
  datasetIds: string[];
  configIds: string[];
  status: BenchmarkStatus;
  startedAt?: string;
  completedAt?: string;
}

export interface StepScore {
  stepId: string;
  stepName: string;
  score: number;
  precision?: number;
  recall?: number;
  f1?: number;
  failedCount: number;
}

export interface BenchmarkRun {
  id: string;
  batchId: string;
  datasetId: string;
  configId: string;
  status: BenchmarkStatus;
  globalScore: number;
  stepScores: StepScore[];
  totalItems: number;
  passedItems: number;
  failedItems: number;
  startedAt: string;
  completedAt?: string;
}

export interface BenchmarkItemResult {
  id: string;
  runId: string;
  tweetId: string;
  tweet: string;
  datasetId: string;
  configId: string;
  passed: boolean;
  expected: string;
  predicted: string;
  confidence?: number;
  stepFailed?: string;
  errorType?: string;
}

export interface HardCase {
  tweetId: string;
  tweet: string;
  datasetId: string;
  totalRuns: number;
  passedRuns: number;
  failedRuns: number;
  passRate: number;
  failedConfigs: string[];
  mainErrorType?: string;
}