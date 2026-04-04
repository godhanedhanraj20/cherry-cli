import { useAuthStore } from '@/features/auth/store';

export const useAuthSession = () => {
  const sessionId = useAuthStore((state) => state.sessionId);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const setSession = useAuthStore((state) => state.setSession);
  const clearSession = useAuthStore((state) => state.clearSession);

  return {
    sessionId,
    hasHydrated,
    setSession,
    clearSession,
  };
};
