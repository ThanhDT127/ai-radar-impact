import { apiClient as api } from './client';

export interface Subscriber {
  id: string;
  email: string;
  roles: string[];
  display_name: string | null;
  active: boolean;
  created_at: string;
}

export interface SubscriberCreate {
  email: string;
  roles: string[];
  display_name?: string | null;
}

export interface SubscriberUpdate {
  roles?: string[];
  active?: boolean;
  display_name?: string | null;
}

export async function fetchSubscribers(): Promise<Subscriber[]> {
  const { data } = await api.get<Subscriber[]>('/subscribers');
  return data;
}

export async function createSubscriber(payload: SubscriberCreate): Promise<Subscriber> {
  const { data } = await api.post<Subscriber>('/subscribers', payload);
  return data;
}

export async function updateSubscriber(
  id: string,
  payload: SubscriberUpdate,
): Promise<Subscriber> {
  const { data } = await api.patch<Subscriber>(`/subscribers/${id}`, payload);
  return data;
}

export async function deleteSubscriber(id: string): Promise<void> {
  await api.delete(`/subscribers/${id}`);
}
