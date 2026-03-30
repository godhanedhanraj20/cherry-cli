'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ROUTES } from '@/constants/routes';
import { sendOtp } from '@/features/auth/api';
import { useAuthSession } from '@/hooks/useAuthSession';
import { handleApiError } from '@/services/error-handler';

export default function LoginPage() {
  const router = useRouter();
  const { setSession } = useAuthSession();

  const [apiId, setApiId] = useState('');
  const [apiHash, setApiHash] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const parsedApiId = Number(apiId);
    if (!Number.isFinite(parsedApiId)) {
      setError('API_ID must be a valid number.');
      return;
    }

    setLoading(true);
    try {
      const response = await sendOtp({
        api_id: parsedApiId,
        api_hash: apiHash.trim(),
        phone_number: phoneNumber.trim(),
      });

      setSession(response.session_id);
      router.push(ROUTES.OTP);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <form onSubmit={onSubmit} style={{ width: '100%', maxWidth: 420, display: 'grid', gap: 12 }}>
        <h1>Login</h1>

        <Input
          type='number'
          placeholder='API_ID'
          value={apiId}
          onChange={(event) => setApiId(event.target.value)}
          required
        />
        <Input
          type='text'
          placeholder='API_HASH'
          value={apiHash}
          onChange={(event) => setApiHash(event.target.value)}
          required
        />
        <Input
          type='text'
          placeholder='Phone number (e.g. +1234567890)'
          value={phoneNumber}
          onChange={(event) => setPhoneNumber(event.target.value)}
          required
        />

        {error ? <p style={{ color: '#b91c1c' }}>{error}</p> : null}

        <Button type='submit' loading={loading}>
          Send OTP
        </Button>
      </form>
    </main>
  );
}
