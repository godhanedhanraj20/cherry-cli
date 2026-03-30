'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { submit2FA } from '@/features/auth/api';
import { useAuthSession } from '@/hooks/useAuthSession';
import { handleApiError } from '@/services/error-handler';

export default function TwoFAPage() {
  const router = useRouter();
  const { sessionId } = useAuthSession();

  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      router.replace('/login');
    }
  }, [router, sessionId]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!sessionId) {
      router.replace('/login');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await submit2FA({ session_id: sessionId, password });
      router.push('/dashboard');
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <form onSubmit={onSubmit} style={{ width: '100%', maxWidth: 420, display: 'grid', gap: 12 }}>
        <h1>Two-Factor Authentication</h1>
        <Input
          type='password'
          placeholder='Password'
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

        <Button type='submit' disabled={loading}>
          {loading ? 'Verifying...' : 'Submit 2FA'}
        </Button>
      </form>
    </main>
  );
}
