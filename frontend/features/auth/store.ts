import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  sessionId: string | null;
  setSession: (sessionId: string) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      sessionId: null,
      setSession: (sessionId: string) => set({ sessionId }),
      clearSession: () => set({ sessionId: null }),
    }),
    {
      name: 'tsg-auth-session',
      partialize: (state) => ({ sessionId: state.sessionId }),
    },
  ),
);
