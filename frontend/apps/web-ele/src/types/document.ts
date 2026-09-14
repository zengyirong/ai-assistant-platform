/** Document types aligned with backend DTO */

export type DocumentStatus =
  | 'UPLOADED'
  | 'PROCESSING'
  | 'READY'
  | 'FAILED'
  | 'DELETED';

export interface DocumentJobBrief {
  id: string;
  status: string;
  progress: number;
  error_code: string | null;
  error_message: string | null;
}

export interface DocumentItem {
  id: string;
  org_id: string;
  kb_id: string;
  file_name: string;
  file_hash: string;
  file_type: string;
  file_size: number;
  page_count: number | null;
  status: DocumentStatus;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
  job_id?: string;
  latest_job?: DocumentJobBrief | null;
}

export interface DocumentPage {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentJob {
  id: string;
  document_id: string;
  job_type: string;
  status: string;
  progress: number;
  retry_count: number;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export const DOCUMENT_STATUS_MAP: Record<
  Exclude<DocumentStatus, 'DELETED'>,
  { label: string; type: 'info' | 'warning' | 'success' | 'danger' }
> = {
  UPLOADED: { label: '已上传', type: 'info' },
  PROCESSING: { label: '解析中', type: 'warning' },
  READY: { label: '已就绪', type: 'success' },
  FAILED: { label: '解析失败', type: 'danger' },
};
