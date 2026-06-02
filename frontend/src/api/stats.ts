import type { InsightStats } from '../types/source';
import { apiClient as api } from './client';

export async function fetchInsightStats(): Promise<InsightStats> {
  const { data } = await api.get<InsightStats>('/insights/stats');
  return data;
}
