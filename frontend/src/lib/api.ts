export class ApiError extends Error {
  readonly status: number;

  readonly code?: string;

  readonly body: unknown;

  constructor(status: number, body: unknown, message: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
    this.code = code;
  }
}

function getBaseUrl(): string {
  const url = import.meta.env.VITE_API_BASE_URL;
  if (!url) {
    throw new Error(
      'VITE_API_BASE_URL is not set. Add it to frontend/.env.development or your shell environment.',
    );
  }
  return url;
}

function extractCode(body: unknown): string | undefined {
  if (body && typeof body === 'object' && 'error' in body) {
    const value = (body as { error: unknown }).error;
    if (typeof value === 'string') return value;
  }
  return undefined;
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function request<T>(
  method: 'GET' | 'POST',
  path: string,
  init?: RequestInit,
  body?: unknown,
): Promise<T> {
  const baseUrl = getBaseUrl();
  const headers = new Headers(init?.headers);
  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      method,
      headers,
      body: payload,
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(0, null, `Network error: ${message}`);
  }

  const parsed = await parseBody(response).catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      parsed,
      `${method} ${path} failed: ${response.status} ${response.statusText}`,
      extractCode(parsed),
    );
  }

  return parsed as T;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>('GET', path, init);
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  init?: RequestInit,
): Promise<T> {
  return request<T>('POST', path, init, body);
}
