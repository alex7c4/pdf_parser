/**
 * Main page component
 */
"use client";

import { useState } from "react";
import FileUpload from "../components/FileUpload";
import DocumentHistory from "../components/DocumentHistory";
import UploadResults from "../components/UploadResults";
import type { UploadResponse } from "../types";

export default function Home(): JSX.Element {
  const [uploadResults, setUploadResults] = useState<UploadResponse[]>([]);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  const handleUploadComplete = (results: UploadResponse[]): void => {
    setUploadResults(results);
  };

  const handleProcessingComplete = (): void => {
    // Refresh history when processing is complete
    setRefreshKey((prev) => prev + 1);
    setUploadResults([]);
  };

  return (
    <main className="container">
      <header className="app-header">
        <h1>PDF Parser & Summarizer</h1>
        <p>Upload PDFs to extract text and generate AI-powered summaries</p>
      </header>

      <div className="content">
        <section className="upload-section">
          <FileUpload onUploadComplete={handleUploadComplete} />
          <UploadResults results={uploadResults} onComplete={handleProcessingComplete} />
        </section>

        <section className="history-section">
          <DocumentHistory key={refreshKey} />
        </section>
      </div>

      <footer className="app-footer">
        <p>Powered by Google Gemini Flash, Mistral OCR, and PyPDF</p>
      </footer>
    </main>
  );
}
