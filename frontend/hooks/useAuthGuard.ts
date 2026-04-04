'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

import { ROUTES } from '@/constants/routes';
import { useAuthSession } from '@/hooks/useAuthSession';

export const useAuthGuard = () => {
  const router = useRouter();
  const { sessionId, hasHydrated } = useAuthSession();
  const redirectedRef = useRef(false);

  useEffect(() => {
    if (!hasHydrated) {
      return;
    }

    if (!sessionId && !redirectedRef.current) {
      redirectedRef.current = true;
      router.replace(ROUTES.LOGIN);
      return;
    }

    if (sessionId) {
      redirectedRef.current = false;
    }
  }, [hasHydrated, router, sessionId]);

  return {
    isCheckingAuth: !hasHydrated,
    isAuthorized: Boolean(sessionId),
  };
};
