// API client for the Insights endpoints

import axios from 'axios';
import type { InsightDetail, InsightListItem, PaginatedResponse } from '../types/insight';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export interface FetchInsightsParams {
  page?: number;
  size?: number;
  role?: string | null;
  source_id?: string | null;
  sort_by?: 'created_at' | 'published_at' | 'impact_label';
}

export async function fetchInsights(
  params: FetchInsightsParams = {}
): Promise<PaginatedResponse<InsightListItem>> {
  const { page = 1, size = 20, role, source_id, sort_by } = params;
  const query: Record<string, string | number> = { page, size };
  if (role) query.role = role;
  if (source_id) query.source_id = source_id;
  if (sort_by) query.sort_by = sort_by;

  const { data } = await api.get<PaginatedResponse<InsightListItem>>('/insights', {
    params: query,
  });
  return data;
}

export async function fetchInsightById(id: string): Promise<InsightDetail> {
  const { data } = await api.get<InsightDetail>(`/insights/${id}`);
  return data;
}
