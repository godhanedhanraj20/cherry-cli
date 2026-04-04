import { API_ROUTES } from '@/constants/api-routes';
import api from '@/services/api';
import type {
  AuthResponse,
  AuthStatusResponse,
  SendOtpRequest,
  SendOtpResponse,
  TwoFARequest,
  VerifyOtpRequest,
} from '@/types/auth';

interface UpdateConfigRequest {
  api_id: string;
  api_hash: string;
}

export const getAuthStatus = async () => {
  const response = await api.get<AuthStatusResponse>(API_ROUTES.AUTH_STATUS);
  return response.data;
};

export const sendOtp = async (payload: SendOtpRequest) => {
  const response = await api.post<SendOtpResponse>(API_ROUTES.AUTH_SEND_OTP, payload);
  return response.data;
};

export const verifyOtp = async (payload: VerifyOtpRequest) => {
  const response = await api.post<AuthResponse>(API_ROUTES.AUTH_VERIFY_OTP, payload);
  return response.data;
};

export const submit2FA = async (payload: TwoFARequest) => {
  const response = await api.post<AuthResponse>(API_ROUTES.AUTH_2FA, payload);
  return response.data;
};

export const logout = async () => {
  try {
    const response = await api.post('/auth/logout');
    return response.data;
  } catch {
    return null;
  }
};

export const updateConfig = async (payload: UpdateConfigRequest) => {
  const response = await api.post('/auth/config', payload);
  return response.data;
};
