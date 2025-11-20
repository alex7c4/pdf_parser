/**
 * Type definitions for PDF Parser application
 */

export type ParserType = "pypdf" | "gemini" | "mistral";

export interface UploadResponse {
  success: boolean;
  message: string;
  pdf_hash: string | null;
  queue_position: number | null;
}

export interface DocumentResponse {
  pdf_hash: string;
  extracted_text: string;
  summary: string;
  original_filename: string;
  parser_type: ParserType;
  status?: string;
  error?: string | null;
}

export interface DocumentStatus {
  pdf_hash: string;
  status: "pending" | "processing" | "completed" | "error";
  message: string | null;
  error?: string | null;
}

export interface HistoryResponse {
  documents: DocumentResponse[];
}

export interface UploadState {
  isUploading: boolean;
  progress: number;
  results: UploadResponse[];
}
