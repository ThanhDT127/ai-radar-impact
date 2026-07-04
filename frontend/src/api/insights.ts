import type { InsightDetail, InsightListItem, PaginatedResponse } from '../types/insight';
import { apiClient as api } from './client';

export interface FetchInsightsParams {
  page?: number;
  size?: number;
  role?: string[] | null;
  source_id?: string[] | null;
  sort_by?: 'urgency' | 'created_at' | 'published_at' | 'impact_label' | 'trust_score' | 'actionability_score';
  urgency?: string[] | null;
  momentum?: string[] | null;
  vietnam_relevance?: string[] | null;
  intelligence_tier?: string[] | null;
  search?: string | null;
}

export async function fetchInsights(
  params: FetchInsightsParams = {}
): Promise<PaginatedResponse<InsightListItem>> {
  const {
    page = 1,
    size = 20,
    role,
    source_id,
    sort_by,
    urgency,
    momentum,
    vietnam_relevance,
    intelligence_tier,
    search,
  } = params;
  const query: Record<string, string | number> = { page, size };

  if (role && role.length > 0) query.role = role.join(',');
  if (source_id && source_id.length > 0) query.source_id = source_id.join(',');
  if (sort_by) query.sort_by = sort_by;
  if (urgency && urgency.length > 0) query.urgency = urgency.join(',');
  if (momentum && momentum.length > 0) query.momentum = momentum.join(',');
  if (vietnam_relevance && vietnam_relevance.length > 0) {
    query.vietnam_relevance = vietnam_relevance.join(',');
  }
  if (intelligence_tier && intelligence_tier.length > 0) {
    query.intelligence_tier = intelligence_tier.join(',');
  }
  if (search) {
    query.search = search;
  }

  const { data } = await api.get<PaginatedResponse<InsightListItem>>('/insights', {
    params: query,
  });
  return data;
}

export async function fetchInsightById(id: string): Promise<InsightDetail> {
  const { data } = await api.get<InsightDetail>(`/insights/${id}`);
  return data;
}
