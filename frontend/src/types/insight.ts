// TypeScript interfaces matching backend Pydantic schemas

export interface InsightListItem {
  id: string;
  title: string;
  summary_short: string | null;
  topics: string[];
  event_type: string | null;
  nature: string | null;
  trust_score: number;
  impact_label: string | null;
  source_url: string;
  confidence: number;
  created_at: string; // ISO 8601 UTC
}

export interface InsightDetail extends InsightListItem {
  summary_medium: string | null;
  status: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  page: number;
  size: number;
  total: number;
  items: T[];
}
