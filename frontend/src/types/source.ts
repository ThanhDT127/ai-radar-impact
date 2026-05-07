export interface SourceListItem {
  id: string;
  name: string;
  source_type: string;
  status: string;
  insight_count: number;
}

export interface InsightStats {
  total: number;
  critical_high: number;
  opportunities: number;
  active_sources: number;
}
