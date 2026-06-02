import axios from 'axios';

// Shared Axios instance — import this in all API modules instead of creating per-file instances.
// Centralising here makes it easy to add interceptors (auth, error handling, logging) later.
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});
