'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { ROUTES } from '@/constants/routes';
import { useAuthSession } from '@/hooks/useAuthSession';

export const useAuthGuard = () => {
  const router = useRouter();
  const { sessionId, hasHydrated } = useAuthSession();

  useEffect(() => {
    if (!hasHydrated) {
      return;
    }

    if (!sessionId) {
      router.replace(ROUTES.LOGIN);
    }
  }, [hasHydrated, router, sessionId]);

  return {
    isCheckingAuth: !hasHydrated,
    isAuthorized: Boolean(sessionId),
  };
};
