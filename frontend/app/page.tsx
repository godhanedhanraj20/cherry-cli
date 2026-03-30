'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { getAuthStatus } from '@/features/auth/api';
import { handleApiError } from '@/services/error-handler';

export default function SplashPage() {
  const router = useRouter();
  const [message, setMessage] = useState('Checking authentication...');

  useEffect(() => {
    let isMounted = true;

    const run = async () => {
      try {
        const status = await getAuthStatus();
        if (!isMounted) return;

        if (status.logged_in) {
          router.replace('/dashboard');
          return;
        }

        router.replace('/login');
      } catch (error) {
        if (!isMounted) return;
        setMessage(handleApiError(error));
        router.replace('/login');
      }
    };

    run();

    return () => {
      isMounted = false;
    };
  }, [router]);

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <p>{message}</p>
    </main>
  );
}
