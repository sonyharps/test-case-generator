// src/types/orchestrator.ts
export interface TestCase {
  tc_id: string;
  title: string;
  preconditions: string[];
  steps: string[];
  expected_result: string[];
}

export interface Risk {
  level: string;
  notes: string[];
}

export interface CoverageMatrix {
  functional_count: number;
  negative_count: number;
  boundary_count: number;
}

export interface OrchestratorResult {
  functional: TestCase[];
  negative: TestCase[];
  boundary: TestCase[];
  summary: string;
  risk: Risk;
  coverage_matrix: CoverageMatrix;
  metadata?: { model?: string; time?: string };
}
