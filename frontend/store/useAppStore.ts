import { create } from 'zustand';

interface AppState {
  globalLoading: boolean;
  resetVersion: number;
  setGlobalLoading: (value: boolean) => void;
  resetAppState: () => void;
}

export const useAppStore = create<AppState>()((set) => ({
  globalLoading: false,
  resetVersion: 0,
  setGlobalLoading: (value) => set({ globalLoading: value }),
  resetAppState: () => set((state) => ({ globalLoading: false, resetVersion: state.resetVersion + 1 })),
}));
