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

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = getBaseUrl();
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, method: 'GET' });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(0, null, `Network error: ${message}`);
  }

  const body = await parseBody(response).catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      body,
      `GET ${path} failed: ${response.status} ${response.statusText}`,
      extractCode(body),
    );
  }

  return body as T;
}
