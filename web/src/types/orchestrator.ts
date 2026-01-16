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

// Warning types for rate limiting and free tier notices
export interface Warning {
  type: string;
  title: string;
  message: string;
  providers?: string[];
}

// Advanced RAG types
export interface Citation {
  id: string;
  text: string;
  score: number;
  metadata: {
    document_id?: number;
    title?: string;
    filename?: string;
    source_collection?: string;
    [key: string]: any;
  };
}

export interface CitationsByCollection {
  documents: Citation[];
  test_cases: Citation[];
  requirements: Citation[];
}

export interface CitationMetadata {
  query_variations: string[];
  collections_searched: string[];
  total_results: number;
  citations_by_collection: CitationsByCollection;
  retrieval_config: {
    query_expansion: boolean;
    reranking: boolean;
    top_k: number;
  };
}

export interface RAGConfig {
  advanced_rag?: boolean;
  basic_rag?: boolean;
  query_expansion?: boolean;
  reranking?: boolean;
  top_k?: number;
  total_docs_retrieved?: number;
}

export interface OrchestratorResult {
  functional: TestCase[];
  negative: TestCase[];
  boundary: TestCase[];
  summary: string;
  risk: Risk;
  coverage_matrix: CoverageMatrix;
  metadata?: { model?: string; time?: string };

  // Advanced RAG fields
  citations?: CitationMetadata;
  rag_config?: RAGConfig;
  session_id?: string;

  // Warnings about rate limiting, free tier mode, etc.
  warnings?: Warning[];
}
