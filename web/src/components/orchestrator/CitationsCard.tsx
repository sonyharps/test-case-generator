import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CitationMetadata } from "@/types/orchestrator";
import { FileText, Book, CheckSquare, Sparkles } from "lucide-react";

interface Props {
  citations: CitationMetadata;
}

export default function CitationsCard({ citations }: Props) {
  const totalCitations = citations.total_results;
  const { documents, test_cases, requirements } = citations.citations_by_collection;

  const allCitations = [
    ...documents.map(c => ({ ...c, collection: "documents" })),
    ...test_cases.map(c => ({ ...c, collection: "test_cases" })),
    ...requirements.map(c => ({ ...c, collection: "requirements" }))
  ].sort((a, b) => b.score - a.score);

  const getCollectionIcon = (collection: string) => {
    switch (collection) {
      case "documents":
        return <FileText className="h-4 w-4" />;
      case "test_cases":
        return <CheckSquare className="h-4 w-4" />;
      case "requirements":
        return <Book className="h-4 w-4" />;
      default:
        return <Sparkles className="h-4 w-4" />;
    }
  };

  const getCollectionColor = (collection: string) => {
    switch (collection) {
      case "documents":
        return "bg-blue-100 text-blue-800";
      case "test_cases":
        return "bg-green-100 text-green-800";
      case "requirements":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            Citations & Sources
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {totalCitations} relevant {totalCitations === 1 ? "document" : "documents"} used to generate test cases
          </p>
        </div>

        <div className="flex gap-2">
          {citations.retrieval_config.query_expansion && (
            <Badge variant="outline" className="bg-blue-50">
              Query Expansion
            </Badge>
          )}
          {citations.retrieval_config.reranking && (
            <Badge variant="outline" className="bg-green-50">
              Re-Ranked
            </Badge>
          )}
        </div>
      </div>

      {/* Query Variations */}
      {citations.query_variations.length > 1 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Also searched for:
          </p>
          <ul className="space-y-1">
            {citations.query_variations.slice(1).map((query, i) => (
              <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="text-gray-400 mt-0.5">•</span>
                <span>{query}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Top Citations */}
      <div className="space-y-3">
        <p className="text-sm font-medium text-gray-700">
          Top sources ({allCitations.length}):
        </p>

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {allCitations.slice(0, 10).map((citation, idx) => (
            <div
              key={citation.id}
              className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${getCollectionColor(citation.collection)}`}>
                      {getCollectionIcon(citation.collection)}
                      {citation.collection.replace("_", " ")}
                    </span>

                    {citation.metadata.title && (
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {citation.metadata.title}
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-gray-600 line-clamp-2">
                    {citation.text}
                  </p>

                  {citation.metadata.filename && (
                    <p className="text-xs text-gray-400 mt-1">
                      From: {citation.metadata.filename}
                    </p>
                  )}
                </div>

                <div className="flex flex-col items-end gap-1">
                  <Badge variant="secondary" className="text-xs">
                    {(citation.score * 100).toFixed(0)}%
                  </Badge>
                  <span className="text-xs text-gray-400">
                    #{idx + 1}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {allCitations.length > 10 && (
          <p className="text-xs text-center text-gray-500 pt-2">
            + {allCitations.length - 10} more sources
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{documents.length}</div>
          <div className="text-xs text-gray-500">Documents</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{test_cases.length}</div>
          <div className="text-xs text-gray-500">Test Cases</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">{requirements.length}</div>
          <div className="text-xs text-gray-500">Requirements</div>
        </div>
      </div>
    </Card>
  );
}
