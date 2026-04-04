'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ROUTES } from '@/constants/routes';
import { submit2FA } from '@/features/auth/api';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { useAuthSession } from '@/hooks/useAuthSession';
import { handleApiError } from '@/services/error-handler';
import { useAppStore } from '@/store/useAppStore';

export default function TwoFAPage() {
  const router = useRouter();
  const { sessionId } = useAuthSession();
  const { isCheckingAuth, isAuthorized } = useAuthGuard();

  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const globalLoading = useAppStore((state) => state.globalLoading);
  const setGlobalLoading = useAppStore((state) => state.setGlobalLoading);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!sessionId) return;

    setError(null);
    setGlobalLoading(true);

    try {
      await submit2FA({ session_id: sessionId, password });
      router.push(ROUTES.DASHBOARD);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setGlobalLoading(false);
    }
  };

  if (isCheckingAuth) {
    return (
      <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <p>Checking session...</p>
      </main>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <form onSubmit={onSubmit} style={{ width: '100%', maxWidth: 420, display: 'grid', gap: 12 }}>
        <h1>Two-Factor Authentication</h1>
        <Input
          type='password'
          placeholder='Password'
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={globalLoading}
          error={Boolean(error)}
          required
        />

        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

        <Button type='submit' loading={globalLoading}>
          Submit 2FA
        </Button>
      </form>
    </main>
  );
}
