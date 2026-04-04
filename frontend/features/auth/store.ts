import { create } from 'zustand';

interface AuthState {
  sessionId: string | null;
  hasHydrated: boolean;
  setSession: (sessionId: string) => void;
  clearSession: () => void;
  resetAuthState: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  sessionId: null,
  hasHydrated: true,
  setSession: (sessionId: string) => set({ sessionId }),
  clearSession: () => set({ sessionId: null }),
  resetAuthState: () => set({ sessionId: null, hasHydrated: true }),
}));
