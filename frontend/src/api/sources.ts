import axios from 'axios';
import type { SourceListItem } from '../types/source';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export async function fetchSources(): Promise<SourceListItem[]> {
  const { data } = await api.get<SourceListItem[]>('/sources');
  return data;
}
