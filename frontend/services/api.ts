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

let hasShownSessionExpired = false;

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiMessage = error?.response?.data?.error;
    const fallbackMessage = typeof apiMessage === 'string' && apiMessage.trim() ? apiMessage : 'Something went wrong';

    if (error?.response?.status === 401) {
      if (!hasShownSessionExpired && typeof window !== 'undefined') {
        hasShownSessionExpired = true;
        window.alert('Session expired. Please login again.');
      }
      useAuthStore.getState().resetAuthState();
      useAppStore.getState().resetAppState();
      if (typeof window !== 'undefined') {
        window.location.href = ROUTES.LOGIN;
      }
    } else if (typeof window !== 'undefined') {
      window.alert(fallbackMessage);
    }
    return Promise.reject(error);
  },
);

export default api;
