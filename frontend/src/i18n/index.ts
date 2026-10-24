import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import enAuth from "@/locales/en/auth.json";
import enCommon from "@/locales/en/common.json";
import enProfile from "@/locales/en/profile.json";
import plAuth from "@/locales/pl/auth.json";
import plCommon from "@/locales/pl/common.json";
import plProfile from "@/locales/pl/profile.json";
import { getSavedLocale } from "@/lib/locale";

// teksty interfejsu: nowy jezyk = nowy folder w locales/
export const resources = {
  pl: { common: plCommon, auth: plAuth, profile: plProfile },
  en: { common: enCommon, auth: enAuth, profile: enProfile },
};

i18n.use(initReactI18next).init({
  resources,
  lng: getSavedLocale(),
  fallbackLng: "pl",
  ns: ["common", "auth", "profile"],
  defaultNS: "common",
  interpolation: { escapeValue: false },
});

export default i18n;
