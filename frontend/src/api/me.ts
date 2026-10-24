import { api } from "@/api/client";
import type { Locale } from "@/lib/locale";
import type { Palette } from "@/lib/palette";

// zalogowany uzytkownik (odpowiedz /api/me)
export type Me = {
  id: string;
  email: string;
  emailVerified: boolean;
  role: string;
  username: string;
  displayName: string;
  avatarUrl: string | null;
  bio: string;
  locale: Locale;
  palette: Palette;
};

export type MeUpdate = Partial<Pick<Me, "username" | "displayName" | "bio" | "locale" | "palette">>;

export const getMe = () => api<Me>("/me");

export const updateMe = (data: MeUpdate) => api<Me>("/me", { method: "PATCH", json: data });

export function uploadAvatar(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api<Me>("/me/avatar", { form });
}

export const deleteAvatar = () => api<Me>("/me/avatar", { method: "DELETE" });

export const changePassword = (currentPassword: string, newPassword: string) =>
  api<{ status: string }>("/me/change-password", { json: { currentPassword, newPassword } });
