import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

interface AuthState {
  sessionId: string | null;
  hasHydrated: boolean;
  setSession: (sessionId: string) => void;
  clearSession: () => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      sessionId: null,
      hasHydrated: false,
      setSession: (sessionId: string) => set({ sessionId }),
      clearSession: () => set({ sessionId: null }),
      setHasHydrated: (value: boolean) => set({ hasHydrated: value }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ sessionId: state.sessionId }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);
