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

export const login = (email: string, password: string) =>
  api<Me>("/auth/login", { json: { email, password } });

export const logout = () => api<void>("/auth/logout", { method: "POST" });

export const verifyEmail = (token: string) =>
  api<Status>("/auth/verify-email", { json: { token } });

export const resendVerification = (email: string) =>
  api<Status>("/auth/resend-verification", { json: { email } });

export const forgotPassword = (email: string) =>
  api<Status>("/auth/forgot-password", { json: { email } });

export const resetPassword = (token: string, password: string) =>
  api<Status>("/auth/reset-password", { json: { token, password } });
