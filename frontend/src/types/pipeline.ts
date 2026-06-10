export type StepStatus =
  | "success"
  | "failed"
  | "warning"
  
  export type AnnotationLabel =
  | "correct"
  | "incorrect"
  | "uncertain"
  
export type RunStatus = "passed" | "blocked" | "warning"
export type TabKey = "recent" | RunStatus

export interface StepAnnotation {
  id: string
  label: AnnotationLabel
  annotatedBy: string
  notes?: string | null
  annotatedAt: string
}

export type PipelineStep = {
  id: string
  // UUID postgres de la step
  stepDbId: string
  name: string
  status: StepStatus
  description: string
  duration: number
  output: Record<string, unknown>
  annotation?: StepAnnotation | null
}

export type PipelineRun = {
  id: string
  text: string
  status: RunStatus
  config: string
  time: string
  createdAt: string
  stoppedAt: string | null
  trace: PipelineStep[]
}