import type { SourceListItem } from '../types/source';
import { apiClient as api } from './client';

export async function fetchSources(): Promise<SourceListItem[]> {
  const { data } = await api.get<SourceListItem[]>('/sources');
  return data;
}
