export interface AuthStatusResponse {
  logged_in: boolean;
  is_premium: boolean;
}

export interface SendOtpRequest {
  api_id: number;
  api_hash: string;
  phone_number: string;
}

export interface SendOtpResponse {
  status: string;
  session_id: string;
}

export interface VerifyOtpRequest {
  session_id: string;
  otp: string;
}

export interface AuthResponse {
  status: string;
  is_premium: boolean;
  requires_2fa: boolean;
  session_id: string | null;
}

export interface TwoFARequest {
  session_id: string;
  password: string;
}
