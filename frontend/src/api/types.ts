export type DocumentRecord = {
  id: number;
  filename: string;
  status: string;
  page_count: number | null;
  file_size: number;
  summary: string | null;
  error_message: string | null;
  created_at: string;
};
