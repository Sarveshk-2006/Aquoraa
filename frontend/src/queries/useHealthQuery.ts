import { useQuery } from '@tanstack/react-query';
import { fetchLiveness, fetchReadiness } from '@/api/client';
import { LivenessResponse, ReadinessResponse } from '@/types/api';

export const healthKeys = {
  all: ['health'] as const,
  liveness: () => [...healthKeys.all, 'liveness'] as const,
  readiness: () => [...healthKeys.all, 'readiness'] as const,
};

export function useLivenessQuery() {
  return useQuery<LivenessResponse>({
    queryKey: healthKeys.liveness(),
    queryFn: fetchLiveness,
    refetchInterval: 30000,
    retry: false,
    refetchOnWindowFocus: false,
  });
}

export function useReadinessQuery() {
  return useQuery<ReadinessResponse>({
    queryKey: healthKeys.readiness(),
    queryFn: fetchReadiness,
    refetchInterval: 30000,
    retry: false,
    refetchOnWindowFocus: false,
  });
}
