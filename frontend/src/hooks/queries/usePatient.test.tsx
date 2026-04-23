import { describe, expect, it } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { usePatient } from './usePatient';

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  Wrapper.displayName = 'TestQueryClientWrapper';
  return Wrapper;
}

describe('usePatient', () => {
  it('does not fetch when patientId is undefined', () => {
    const { result } = renderHook(() => usePatient(undefined), {
      wrapper: makeWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(result.current.status).toBe('pending');
    expect(result.current.data).toBeUndefined();
  });
});
