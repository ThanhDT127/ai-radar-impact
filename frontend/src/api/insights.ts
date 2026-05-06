// API client for the Insights endpoints

import axios from 'axios';
import type { InsightDetail, InsightListItem, PaginatedResponse } from '../types/insight';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export async function fetchInsights(
  page = 1,
  size = 20
): Promise<PaginatedResponse<InsightListItem>> {
  const { data } = await api.get<PaginatedResponse<InsightListItem>>('/insights', {
    params: { page, size },
  });
  return data;
}

export async function fetchInsightById(id: string): Promise<InsightDetail> {
  const { data } = await api.get<InsightDetail>(`/insights/${id}`);
  return data;
}
