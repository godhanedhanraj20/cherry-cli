'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { verifyOtp } from '@/features/auth/api';
import { useAuthSession } from '@/hooks/useAuthSession';
import { handleApiError } from '@/services/error-handler';

export default function OtpPage() {
  const router = useRouter();
  const { sessionId } = useAuthSession();

  const [otp, setOtp] = useState('');
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
      const response = await verifyOtp({ session_id: sessionId, otp: otp.trim() });

      if (response.requires_2fa) {
        router.push('/2fa');
        return;
      }

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
        <h1>OTP Verification</h1>
        <Input
          type='text'
          inputMode='numeric'
          maxLength={5}
          placeholder='Enter 5-digit OTP'
          value={otp}
          onChange={(event) => setOtp(event.target.value)}
          required
        />

        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

        <Button type='submit' disabled={loading}>
          {loading ? 'Verifying...' : 'Verify OTP'}
        </Button>
      </form>
    </main>
  );
}
