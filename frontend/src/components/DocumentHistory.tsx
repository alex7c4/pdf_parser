/**
 * Document history component
 */
"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { DocumentResponse } from "../types";
import { ApiService } from "../services/api";

export default function DocumentHistory(): JSX.Element {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  const loadHistory = async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response = await ApiService.getHistory();
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
    // Poll for updates every 5 seconds
    const interval = setInterval(loadHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleExpand = (pdfHash: string): void => {
    setExpandedDoc(expandedDoc === pdfHash ? null : pdfHash);
  };

  if (loading && documents.length === 0) {
    return (
      <div className="history-container">
        <h2>Recent Documents</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-container">
        <h2>Recent Documents</h2>
        <div className="error-message">{error}</div>
        <button onClick={loadHistory} className="btn-secondary">
          Retry
        </button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="history-container">
        <h2>Recent Documents</h2>
        <p>No documents processed yet. Upload a PDF to get started!</p>
      </div>
    );
  }

  return (
    <div className="history-container">
      <div className="history-header">
        <h2>Recent Documents (Last 10)</h2>
        <button onClick={loadHistory} className="btn-secondary btn-small">
          Refresh
        </button>
      </div>

      <div className="document-list">
        {documents.map((doc) => (
          <div key={doc.pdf_hash} className={`document-card ${doc.status === 'error' ? 'error-card' : ''}`}>
            <div className="document-header">
              <div>
                <h3>{doc.original_filename || doc.pdf_hash}</h3>
                <div className="document-meta">
                  <span className="parser-badge">{doc.parser_type}</span>
                  <span className="doc-key-badge">{doc.pdf_hash}</span>
                  {doc.status === 'error' && <span className="status-badge error">Error</span>}
                </div>
              </div>
              {doc.status !== 'error' && (
                <button onClick={() => toggleExpand(doc.pdf_hash)} className="btn-expand">
                  {expandedDoc === doc.pdf_hash ? "Hide" : "Show"} Full Text
                </button>
              )}
            </div>

            {doc.status === 'error' && doc.error && (
              <div className="error-message">
                <h4>Processing Error:</h4>
                <p>{doc.error}</p>
              </div>
            )}

            {doc.status !== 'error' && (
              <>
                <div className="document-summary">
                  <h4>Summary:</h4>
                  <ReactMarkdown>{doc.summary}</ReactMarkdown>
                </div>

                {expandedDoc === doc.pdf_hash && (
                  <div className="document-details">
                    <h4>Full Extracted Text:</h4>
                    <pre className="extracted-text-code">
                      <code>{doc.extracted_text}</code>
                    </pre>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
