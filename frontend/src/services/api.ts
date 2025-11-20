/**
 * API service for communicating with backend
 */

import type { DocumentResponse, DocumentStatus, HistoryResponse, ParserType, UploadResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiService {
  /**
   * Upload PDF files
   */
  static async uploadFiles(files: File[], parserType: ParserType): Promise<UploadResponse[]> {
    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });
    formData.append("parser_type", parserType);

    const response = await fetch(`${API_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get document by hash
   */
  static async getDocument(pdfHash: string): Promise<DocumentResponse> {
    const response = await fetch(`${API_URL}/document/${pdfHash}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch document: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get document status
   */
  static async getStatus(pdfHash: string): Promise<DocumentStatus> {
    const response = await fetch(`${API_URL}/status/${pdfHash}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch status: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get processing history
   */
  static async getHistory(): Promise<HistoryResponse> {
    const response = await fetch(`${API_URL}/history`);

    if (!response.ok) {
      throw new Error(`Failed to fetch history: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Health check
   */
  static async healthCheck(): Promise<{ status: string; redis: string }> {
    const response = await fetch(`${API_URL}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }
}
