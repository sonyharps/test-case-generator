// src/pages/DocumentsPage.tsx
import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/store/auth.store";
import {
  uploadDocument,
  listDocuments,
  getDocument,
  deleteDocument,
  type DocumentSummary,
  type DocumentDetail,
} from "@/api/documents";
import { useDocumentEvents } from "@/hooks/useDocumentEvents";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Upload,
  FileText,
  Trash2,
  Eye,
  CheckCircle,
  AlertCircle,
  Clock,
  Loader2,
  X,
  Timer,
} from "lucide-react";

// Helper to format elapsed time
function formatElapsedTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

// Hook to track elapsed time for processing documents
function useElapsedTime(isProcessing: boolean, startTime: Date | null) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isProcessing || !startTime) return;

    const updateElapsed = () => {
      const now = new Date();
      const diff = Math.floor((now.getTime() - new Date(startTime).getTime()) / 1000);
      setElapsed(diff);
    };

    // Update immediately
    updateElapsed();

    // Update every second
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [isProcessing, startTime]);

  return elapsed;
}

// Document Item Component with Elapsed Time
function DocumentItem({ doc, onView, onDelete }: {
  doc: DocumentSummary;
  onView: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  const isProcessing = doc.processing_status === "processing" || doc.processing_status === "pending";
  const elapsed = useElapsedTime(isProcessing, doc.created_at ? new Date(doc.created_at) : null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-50 text-green-700 border-green-200";
      case "processing":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "pending":
        return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "failed":
        return "bg-red-50 text-red-700 border-red-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "processing":
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case "pending":
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4 flex-1">
            <FileText className="w-10 h-10 text-blue-600 flex-shrink-0 mt-1" />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold text-gray-900 truncate">
                  {doc.title || doc.filename}
                </h3>
                <span
                  className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(
                    doc.processing_status
                  )}`}
                >
                  {doc.processing_status}
                </span>
                {isProcessing && (
                  <span className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                    <Timer className="w-3 h-3" />
                    {formatElapsedTime(elapsed)}
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-600 mb-2">{doc.filename}</p>

              {doc.content_preview && (
                <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                  {doc.content_preview}
                </p>
              )}

              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>{doc.file_type.toUpperCase()}</span>
                <span>•</span>
                <span>{doc.requirement_count} requirements</span>
                <span>•</span>
                <span>
                  {new Date(doc.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
            {getStatusIcon(doc.processing_status)}

            <Button
              size="sm"
              variant="outline"
              onClick={() => onView(doc.id)}
            >
              <Eye className="w-4 h-4" />
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => onDelete(doc.id)}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DocumentsPage() {
  const accessToken = useAuth((state) => state.accessToken);

  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Modal state
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Setup real-time event listener
  useDocumentEvents({
    onDocumentUpdate: (event) => {
      // Refresh document list when processing completes or fails
      if (event.status === 'completed' || event.status === 'failed') {
        loadDocuments();
      }
    },
  });

  useEffect(() => {
    if (accessToken) {
      loadDocuments();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await listDocuments(accessToken!, 0, 50);
      setDocuments(response.documents);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];

    // Validate file type
    const allowedTypes = ["pdf", "docx", "txt", "md"];
    const extension = file.name.split(".").pop()?.toLowerCase();

    if (!extension || !allowedTypes.includes(extension)) {
      setError(
        `Unsupported file type: .${extension}. Allowed: ${allowedTypes.join(", ")}`
      );
      return;
    }

    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setError("File size exceeds 50MB limit");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadDocument(file, accessToken!, true);

      // Reload documents list
      await loadDocuments();

      // Show success message
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    handleFileSelect(files);
  }, [accessToken]);

  const handleViewDocument = async (docId: number) => {
    setLoadingDetail(true);
    setShowDetailModal(true);

    try {
      const doc = await getDocument(docId, accessToken!);
      setSelectedDocument(doc);
    } catch (err: any) {
      setError(err.message || "Failed to load document details");
      setShowDetailModal(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return;

    try {
      await deleteDocument(docId, accessToken!);
      await loadDocuments();
    } catch (err: any) {
      setError(err.message || "Failed to delete document");
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Documents</h2>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Documents</h2>
        <p className="text-gray-600 mt-1">
          Upload PRDs, user stories, and other documents for AI-powered test case generation
        </p>
      </div>

      {/* Upload Area */}
      <Card
        className={`border-2 border-dashed transition-all ${
          dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="p-8 text-center">
          {uploading ? (
            <div className="space-y-4">
              <Loader2 className="w-12 h-12 mx-auto text-blue-600 animate-spin" />
              <p className="text-gray-600">Uploading and processing document...</p>
            </div>
          ) : (
            <>
              <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                Drop your document here or click to browse
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Supported: PDF, Word (.docx), Markdown (.md), Text (.txt) • Max 50MB
              </p>
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".pdf,.docx,.md,.txt"
                onChange={(e) => handleFileSelect(e.target.files)}
                disabled={uploading}
              />
              <label htmlFor="file-upload">
                <Button asChild disabled={uploading}>
                  <span className="cursor-pointer">
                    <Upload className="w-4 h-4 mr-2" />
                    Choose File
                  </span>
                </Button>
              </label>
            </>
          )}
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Documents List */}
      {documents.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">No documents yet</p>
            <p className="text-sm mt-2">Upload your first document to get started</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {documents.map((doc) => (
            <DocumentItem
              key={doc.id}
              doc={doc}
              onView={handleViewDocument}
              onDelete={handleDeleteDocument}
            />
          ))}
        </div>
      )}

      {/* Document Detail Modal */}
      {showDetailModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-4xl max-h-[90vh] flex flex-col">
            <CardContent className="p-6 flex flex-col min-h-0 flex-1">
              <div className="flex justify-between items-start mb-4 flex-shrink-0">
                <h3 className="text-xl font-bold">
                  {selectedDocument?.title || selectedDocument?.filename}
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDetailModal(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {loadingDetail ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                </div>
              ) : selectedDocument ? (
                <div className="space-y-4 overflow-y-auto flex-1 min-h-0 pr-2">
                  {/* Metadata */}
                  <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">File Type</p>
                      <p className="font-medium">{selectedDocument.file_type.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">File Size</p>
                      <p className="font-medium">{formatFileSize(selectedDocument.file_size)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Requirements</p>
                      <p className="font-medium">{selectedDocument.requirement_count}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Chunks</p>
                      <p className="font-medium">{selectedDocument.chunk_count}</p>
                    </div>
                  </div>

                  {/* Extracted Requirements */}
                  {selectedDocument.extracted_requirements && selectedDocument.extracted_requirements.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">
                        Extracted Requirements ({selectedDocument.extracted_requirements.length})
                      </h4>
                      <div className="space-y-3">
                        {selectedDocument.extracted_requirements.map((req, idx) => (
                          <Card key={idx} className="border-l-4 border-l-blue-500">
                            <CardContent className="p-4">
                              <h5 className="font-medium text-gray-900 mb-2">{req.title}</h5>
                              <p className="text-sm text-gray-600 mb-2">{req.description}</p>
                              {req.acceptance_criteria.length > 0 && (
                                <div className="mt-2">
                                  <p className="text-xs font-medium text-gray-700 mb-1">
                                    Acceptance Criteria:
                                  </p>
                                  <ul className="text-xs text-gray-600 list-disc list-inside">
                                    {req.acceptance_criteria.map((ac, i) => (
                                      <li key={i}>{ac}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sections */}
                  {selectedDocument.sections && selectedDocument.sections.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Document Sections</h4>
                      <div className="space-y-2">
                        {selectedDocument.sections.map((section, idx) => (
                          <details key={idx} className="border rounded-lg p-3">
                            <summary className="font-medium cursor-pointer">
                              {section.heading}
                            </summary>
                            <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                              {section.content}
                            </p>
                          </details>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
