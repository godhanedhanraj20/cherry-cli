import axios from 'axios';
import { ROUTES } from '@/constants/routes';
import { useAuthStore } from '@/features/auth/store';
import { useAppStore } from '@/store/useAppStore';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      useAuthStore.getState().resetAuthState();
      useAppStore.getState().resetAppState();
      if (typeof window !== 'undefined') {
        window.location.href = ROUTES.LOGIN;
      }
    }
    return Promise.reject(error);
  },
);

export default api;
