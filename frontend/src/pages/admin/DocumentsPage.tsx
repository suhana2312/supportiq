import React, { useState, useEffect } from "react";
import { apiRequest } from "../../services/api";
import { Document, DocumentStatus } from "../../types";
import {
  UploadCloud,
  FileText,
  Trash2,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  FileCode,
  Layers
} from "lucide-react";

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isDragOver, setIsDragOver] = useState(false);

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(loadDocuments, 5000); // Polling for processing status
    return () => clearInterval(interval);
  }, []);

  const loadDocuments = async () => {
    try {
      const res = await apiRequest<{ items: Document[] }>("/documents", {
        params: { page: 1, page_size: 50 }
      });
      setDocuments(res.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    try {
      await apiRequest("/documents", {
        method: "POST",
        body: formData
      });
      loadDocuments();
    } catch (err: any) {
      alert(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await apiRequest(`/documents/${id}/reprocess`, { method: "POST" });
      loadDocuments();
    } catch (e: any) {
      alert(e.message || "Failed to trigger reprocess");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to permanently delete this document and its vector chunks?")) return;
    try {
      await apiRequest(`/documents/${id}`, { method: "DELETE" });
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (e: any) {
      alert(e.message || "Failed to delete document");
    }
  };

  const getStatusBadge = (status: DocumentStatus) => {
    switch (status) {
      case "PROCESSED":
        return <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Processed</span>;
      case "PROCESSING":
        return <span className="bg-blue-50 text-blue-700 border border-blue-200 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1 animate-pulse"><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Processing Chunks...</span>;
      case "FAILED":
        return <span className="bg-rose-50 text-rose-700 border border-rose-200 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" /> Failed</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 text-xs px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Uploaded</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Knowledge Base & Document Ingestion</h1>
        <p className="text-sm text-slate-500">
          Upload PDF, DOCX, TXT, or Markdown documents to be vectorized into pgvector embeddings for RAG retrieval.
        </p>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          handleFileUpload(e.dataTransfer.files);
        }}
        className={`border-2 border-dashed rounded-2xl p-8 text-center transition flex flex-col items-center justify-center cursor-pointer ${
          isDragOver
            ? "border-indigo-500 bg-indigo-50/50"
            : "border-slate-300 hover:border-slate-400 bg-white"
        }`}
      >
        <input
          type="file"
          id="fileUploadInput"
          className="hidden"
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => handleFileUpload(e.target.files)}
        />
        <label htmlFor="fileUploadInput" className="cursor-pointer flex flex-col items-center">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
            <UploadCloud className="w-7 h-7" />
          </div>
          <span className="font-semibold text-sm text-slate-800">
            {uploading ? "Ingesting & Chunking Document..." : "Click to upload or drag & drop documentation"}
          </span>
          <span className="text-xs text-slate-400 mt-1">
            Supported formats: PDF, DOCX, Markdown, TXT (Maximum 15MB)
          </span>
        </label>
      </div>

      {/* Document Records Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-bold text-sm text-slate-900">Ingested Company Documents ({documents.length})</h3>
          <button
            onClick={loadDocuments}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-500 text-xs flex items-center gap-1 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No documents uploaded yet. Upload your first policy or manual above!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Size</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Chunks</th>
                  <th className="py-3 px-4">Uploaded Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3.5 px-4 font-semibold text-slate-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-500 shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="py-3.5 px-4 uppercase font-mono text-[11px] text-slate-500">{doc.file_type}</td>
                    <td className="py-3.5 px-4">{(doc.file_size / 1024).toFixed(1)} KB</td>
                    <td className="py-3.5 px-4">{getStatusBadge(doc.status)}</td>
                    <td className="py-3.5 px-4 font-medium text-indigo-700">
                      <span className="flex items-center gap-1">
                        <Layers className="w-3.5 h-3.5" /> {doc.chunk_count || "Ready"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      {doc.status === "FAILED" && (
                        <button
                          onClick={() => handleReprocess(doc.id)}
                          className="px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded text-[11px] font-semibold transition"
                          title="Retry Processing"
                        >
                          Retry
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1 hover:text-rose-600 text-slate-400 rounded transition"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
