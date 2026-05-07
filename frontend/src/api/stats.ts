import axios from 'axios';
import type { InsightStats } from '../types/source';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export async function fetchInsightStats(): Promise<InsightStats> {
  const { data } = await api.get<InsightStats>('/insights/stats');
  return data;
}
