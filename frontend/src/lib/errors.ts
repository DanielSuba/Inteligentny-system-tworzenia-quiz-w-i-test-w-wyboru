import i18n from "i18next";
import { ApiError } from "@/api/client";

// zamienia blad z API na tekst w jezyku uzytkownika
export function errorText(e: unknown): string {
  const code = e instanceof ApiError ? e.code : "server_error";
  const key = `common:errors.${code}`;
  return i18n.exists(key) ? i18n.t(key) : i18n.t("common:errors.server_error");
}
