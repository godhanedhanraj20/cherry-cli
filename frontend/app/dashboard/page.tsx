'use client';

import { useAuthGuard } from '@/hooks/useAuthGuard';

export default function DashboardPage() {
  const { isCheckingAuth, isAuthorized } = useAuthGuard();

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
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <h1>Dashboard</h1>
    </main>
  );
}
