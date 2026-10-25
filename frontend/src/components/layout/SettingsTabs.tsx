import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";
import { cn } from "@/lib/utils";

// zakladki ustawien: ogolne i bezpieczenstwo
export function SettingsTabs() {
  const { t } = useTranslation();
  const tab = ({ isActive }: { isActive: boolean }) =>
    cn(
      "border-b-2 px-3 py-1.5",
      isActive ? "border-acc text-fg" : "border-transparent text-mut hover:text-fg",
    );
  return (
    <nav className="flex gap-1 border-b border-line">
      <NavLink to="/settings" end className={tab}>
        {t("nav.general")}
      </NavLink>
      <NavLink to="/settings/security" className={tab}>
        {t("nav.security")}
      </NavLink>
    </nav>
  );
}
