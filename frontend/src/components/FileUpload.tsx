/**
 * File upload component
 */
"use client";

import { useState } from "react";
import type { ParserType, UploadResponse } from "../types";
import { ApiService } from "../services/api";

interface FileUploadProps {
  onUploadComplete: (results: UploadResponse[]) => void;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps): JSX.Element {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [parserType, setParserType] = useState<ParserType>("gemini");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files) {
      const files = Array.from(e.target.files);

      // Validate file types
      const invalidFiles = files.filter((file) => !file.name.toLowerCase().endsWith(".pdf"));
      if (invalidFiles.length > 0) {
        setError("Only PDF files are allowed");
        return;
      }

      // Validate file sizes
      const largeFiles = files.filter((file) => file.size > 26214400); // 25MB
      if (largeFiles.length > 0) {
        setError("Some files exceed the 25MB size limit");
        return;
      }

      // Validate total count
      if (files.length > 50) {
        setError("Maximum 50 files allowed per upload");
        return;
      }

      setSelectedFiles(files);
      setError(null);
    }
  };

  const handleUpload = async (): Promise<void> => {
    if (selectedFiles.length === 0) {
      setError("Please select at least one file");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const results = await ApiService.uploadFiles(selectedFiles, parserType);
      onUploadComplete(results);
      setSelectedFiles([]);

      // Reset file input
      const fileInput = document.getElementById("file-input") as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload PDF Documents</h2>

      <div className="form-group">
        <label htmlFor="parser-select">Parser Type:</label>
        <select
          id="parser-select"
          value={parserType}
          onChange={(e) => setParserType(e.target.value as ParserType)}
          disabled={isUploading}
        >
          <option value="gemini">Google Gemini Flash (Markdown) - Default</option>
          <option value="mistral">Mistral (Markdown)</option>
          <option value="pypdf">PyPDF (Plain Text)</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="file-input">Select PDF Files:</label>
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileChange}
          disabled={isUploading}
        />
        {selectedFiles.length > 0 && (
          <div className="file-list">
            <p>Selected {selectedFiles.length} file(s):</p>
            <ul>
              {selectedFiles.slice(0, 5).map((file, idx) => (
                <li key={idx}>
                  {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </li>
              ))}
              {selectedFiles.length > 5 && <li>... and {selectedFiles.length - 5} more</li>}
            </ul>
          </div>
        )}
      </div>

      <button onClick={handleUpload} disabled={isUploading || selectedFiles.length === 0} className="btn-primary">
        {isUploading ? "Uploading..." : "Upload & Process"}
      </button>

      {error && <div className="error-message">{error}</div>}

      <div className="info-box">
        <p>
          <strong>Limits:</strong>
        </p>
        <ul>
          <li>Maximum 50 files per upload</li>
          <li>Maximum 25MB per file</li>
          <li>PDF files only</li>
          <li>Maximum 5 concurrent processing tasks</li>
        </ul>
      </div>
    </div>
  );
}
