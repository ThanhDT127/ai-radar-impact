export interface InsightListItem {
  id: string;
  title: string;
  summary_short: string | null;
  summary_medium: string | null;
  topics: string[];
  event_type: string | null;
  nature: string | null;
  trust_score: number;
  impact_label: string | null;
  source_url: string;
  confidence: number;
  affected_roles: string[];
  published_at: string | null;
  created_at: string;
  source_id: string;
  source_name: string;
  source_type: string;
}

export interface InsightDetail extends InsightListItem {
  summary_medium: string | null;
  status: string;
  updated_at: string;
  source_feed_url: string | null;
}

export interface PaginatedResponse<T> {
  page: number;
  size: number;
  total: number;
  items: T[];
}
