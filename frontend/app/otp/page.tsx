'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ROUTES } from '@/constants/routes';
import { verifyOtp } from '@/features/auth/api';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { useAuthSession } from '@/hooks/useAuthSession';
import { handleApiError } from '@/services/error-handler';
import { useAppStore } from '@/store/useAppStore';

export default function OtpPage() {
  const router = useRouter();
  const { sessionId } = useAuthSession();
  const { isCheckingAuth, isAuthorized } = useAuthGuard();

  const [otp, setOtp] = useState('');
  const [error, setError] = useState<string | null>(null);
  const globalLoading = useAppStore((state) => state.globalLoading);
  const setGlobalLoading = useAppStore((state) => state.setGlobalLoading);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!sessionId) return;

    setError(null);
    setGlobalLoading(true);

    try {
      const response = await verifyOtp({ session_id: sessionId, otp: otp.trim() });

      if (response.requires_2fa) {
        router.push(ROUTES.TWO_FA);
        return;
      }

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
        <h1>OTP Verification</h1>
        <Input
          type='text'
          inputMode='numeric'
          maxLength={5}
          placeholder='Enter 5-digit OTP'
          value={otp}
          onChange={(event) => setOtp(event.target.value)}
          disabled={globalLoading}
          error={Boolean(error)}
          required
        />

        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

        <Button type='submit' loading={globalLoading}>
          Verify OTP
        </Button>
      </form>
    </main>
  );
}
