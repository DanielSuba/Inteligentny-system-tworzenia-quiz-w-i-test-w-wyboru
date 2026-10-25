import { api } from "@/api/client";
import type { Me } from "@/api/me";
import type { Locale } from "@/lib/locale";

type Status = { status: string };

export type RegisterData = {
  email: string;
  password: string;
  username: string;
  displayName?: string;
  locale: Locale;
};

export const register = (data: RegisterData) => api<Status>("/auth/register", { json: data });

// konto z 2FA zwraca { status: "2fa_required" } zamiast uzytkownika
export const login = (email: string, password: string) =>
  api<Me | Status>("/auth/login", { json: { email, password } });

// drugi krok logowania: kod z aplikacji albo kod zapasowy
export const loginCode = (code: string) => api<Me>("/auth/login/2fa", { json: { code } });

export const logout = () => api<void>("/auth/logout", { method: "POST" });

export const verifyEmail = (token: string) =>
  api<Status>("/auth/verify-email", { json: { token } });

export const resendVerification = (email: string) =>
  api<Status>("/auth/resend-verification", { json: { email } });

export const forgotPassword = (email: string) =>
  api<Status>("/auth/forgot-password", { json: { email } });

export const resetPassword = (token: string, password: string) =>
  api<Status>("/auth/reset-password", { json: { token, password } });
