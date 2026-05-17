export interface RoutineResult { status: string; steps: StepResult[]; report: string; created_at: string; }
export interface StepResult { step_id: string; name: string; status: string; data: any; duration_ms: number; error?: string; }
