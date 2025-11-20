/**
 * Upload results component
 */
"use client";

import { useEffect, useState } from "react";
import type { DocumentStatus, UploadResponse } from "../types";
import { ApiService } from "../services/api";

interface UploadResultsProps {
  results: UploadResponse[];
  onComplete: () => void;
}

export default function UploadResults({ results, onComplete }: UploadResultsProps): JSX.Element {
  const [statuses, setStatuses] = useState<Map<string, DocumentStatus>>(new Map());

  useEffect(() => {
    if (results.length === 0) return;

    // Poll for status updates
    const interval = setInterval(async () => {
      const newStatuses = new Map(statuses);
      let allCompleted = true;

      for (const result of results) {
        if (result.success && result.pdf_hash) {
          try {
            const status = await ApiService.getStatus(result.pdf_hash);
            newStatuses.set(result.pdf_hash, status);

            if (status.status !== "completed" && status.status !== "error") {
              allCompleted = false;
            }
          } catch (err) {
            console.error("Failed to fetch status:", err);
            allCompleted = false;
          }
        }
      }

      setStatuses(newStatuses);

      if (allCompleted) {
        clearInterval(interval);
        // Notify parent that processing is complete
        setTimeout(onComplete, 1000);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [results]);

  if (results.length === 0) return <></>;

  return (
    <div className="upload-results">
      <h3>Upload Results</h3>

      <div className="results-list">
        {results.map((result, idx) => (
          <div key={idx} className={`result-item ${result.success ? "success" : "error"}`}>
            <div className="result-message">
              <span className={`status-icon ${result.success ? "success" : "error"}`}>
                {result.success ? "✓" : "✗"}
              </span>
              <span>{result.message}</span>
            </div>

            {result.pdf_hash && statuses.has(result.pdf_hash) && (
              <div className="status-info">
                {(() => {
                  const status = statuses.get(result.pdf_hash)!;
                  return (
                    <>
                      <span className={`status-badge ${status.status}`}>{status.status}</span>
                      {status.status === "pending" && <span className="spinner">⟳</span>}
                      {status.status === "processing" && <span className="spinner">⟳</span>}
                      {status.status === "completed" && <span className="check-mark">✓</span>}
                      {status.status === "error" && status.error && (
                        <div className="error-details">
                          <span className="error-icon">⚠</span>
                          <span className="error-text">{status.error}</span>
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
