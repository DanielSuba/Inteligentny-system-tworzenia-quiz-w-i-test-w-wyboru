import { api } from "@/api/client";

export type TwoFactorStatus = { enabled: boolean; backupCodesLeft: number; stepUpActive: boolean };
export type Setup = { secret: string; uri: string; qr: string };
export type Provider = "openrouter" | "openai" | "anthropic" | "google";

export type ApiKey = {
  id: string;
  provider: Provider;
  label: string;
  last4: string;
  createdAt: string;
  lastUsedAt: string | null;
};

export type AuditEntry = { action: string; detail: string; ip: string; createdAt: string };

export type Model = {
  provider: string;
  id: string;
  name: string;
  context: number | null;
  priceIn: number | null;
  priceOut: number | null;
  source: "user" | "system" | "local";
};

// 2FA
export const getTwoFactor = () => api<TwoFactorStatus>("/me/2fa");
export const setupTwoFactor = () => api<Setup>("/me/2fa/setup", { method: "POST" });
export const enableTwoFactor = (code: string) =>
  api<{ codes: string[] }>("/me/2fa/enable", { json: { code } });
export const disableTwoFactor = (code: string) =>
  api<TwoFactorStatus>("/me/2fa/disable", { json: { code } });
export const newBackupCodes = (code: string) =>
  api<{ codes: string[] }>("/me/2fa/backup-codes", { json: { code } });
export const stepUp = (code: string) => api<TwoFactorStatus>("/me/2fa/verify", { json: { code } });

// klucze API
export const listKeys = () => api<ApiKey[]>("/me/api-keys");
export const addKey = (provider: Provider, key: string, label: string) =>
  api<ApiKey>("/me/api-keys", { json: { provider, key, label } });
export const deleteKey = (id: string) => api<void>(`/me/api-keys/${id}`, { method: "DELETE" });

export const getAudit = () => api<AuditEntry[]>("/me/audit");
export const getModels = () => api<Model[]>("/ai/models");
