import { useAuthStore } from '@/features/auth/store';

export const useAuthSession = () => {
  const sessionId = useAuthStore((state) => state.sessionId);
  const setSession = useAuthStore((state) => state.setSession);
  const clearSession = useAuthStore((state) => state.clearSession);

  return {
    sessionId,
    setSession,
    clearSession,
  };
};
