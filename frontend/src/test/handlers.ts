import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('http://localhost:8000/patients', () =>
    HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 }),
  ),
];
