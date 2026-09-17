import { LivenessResponse, ReadinessResponse, ApiErrorResponse } from '@/types/api';

export class ApiClientError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly requestId?: string;

  constructor(message: string, statusCode: number, code: string = 'API_ERROR', requestId?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.statusCode = statusCode;
    this.code = code;
    this.requestId = requestId;
  }
}

const rawApiUrl = import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL = (rawApiUrl && rawApiUrl.trim() !== '')
  ? rawApiUrl.replace(/\/$/, '')
  : (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      ? `${window.location.protocol}//${window.location.hostname}:8000`
      : '');

function generateRequestId(): string {
  return 'req-' + Math.random().toString(36).substring(2, 10);
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const requestId = generateRequestId();
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', requestId);
  }

  const url = API_BASE_URL ? `${API_BASE_URL}${endpoint}` : endpoint;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const responseRequestId = response.headers.get('X-Request-ID') || requestId;

    if (!response.ok && response.status !== 503) {
      let errorPayload: ApiErrorResponse | null = null;
      try {
        errorPayload = await response.json();
      } catch {
        // Fallback if response body is not JSON
      }

      const code = errorPayload?.error?.code || `HTTP_${response.status}`;
      const message = errorPayload?.error?.message || `API request failed with status ${response.status}`;
      throw new ApiClientError(message, response.status, code, responseRequestId);
    }

    const data: T = await response.json();
    return data;
  } catch (error: unknown) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    if (error instanceof Error) {
      throw new ApiClientError(`Network Error: ${error.message}`, 0, 'NETWORK_ERROR', requestId);
    }
    throw new ApiClientError('An unknown error occurred', 0, 'UNKNOWN_ERROR', requestId);
  }
}

export async function apiUploadFormData<T>(endpoint: string, formData: FormData): Promise<T> {
  const requestId = generateRequestId();
  const headers = new Headers();
  headers.set('Accept', 'application/json');
  headers.set('X-Request-ID', requestId);

  const url = API_BASE_URL ? `${API_BASE_URL}${endpoint}` : endpoint;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    const responseRequestId = response.headers.get('X-Request-ID') || requestId;

    if (!response.ok) {
      let message = `Upload failed with status ${response.status}`;
      try {
        const err = await response.json();
        if (err?.error?.message) message = err.error.message;
      } catch {}
      throw new ApiClientError(message, response.status, `HTTP_${response.status}`, responseRequestId);
    }

    return response.json();
  } catch (error: unknown) {
    if (error instanceof ApiClientError) throw error;
    if (error instanceof Error) throw new ApiClientError(`Upload failed: ${error.message}`, 0, 'NETWORK_ERROR', requestId);
    throw new ApiClientError('Upload failed with unknown error', 0, 'UNKNOWN_ERROR', requestId);
  }
}

export async function fetchLiveness(): Promise<LivenessResponse> {
  return apiFetch<LivenessResponse>('/api/v1/health/live');
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  return apiFetch<ReadinessResponse>('/api/v1/health/ready');
}

// Backward compatibility helper
export async function fetchHealthStatus(): Promise<ReadinessResponse> {
  return fetchReadiness();
}
