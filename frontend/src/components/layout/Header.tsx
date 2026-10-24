import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, useNavigate } from "react-router";
import { LangSwitch } from "@/components/layout/LangSwitch";
import { Avatar } from "@/components/ui/Avatar";
import { Logo } from "@/components/ui/Logo";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const linkStyle = ({ isActive }: { isActive: boolean }) =>
  cn("flex items-center gap-2 px-2 py-1.5 hover:text-fg", isActive ? "text-fg" : "text-mut");

// gorny pasek: logo, nawigacja, jezyk, konto; na telefonie menu rozwijane
export function Header() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  async function doLogout() {
    setOpen(false);
    await logout();
    navigate("/");
  }

  const links = user ? (
    <>
      <NavLink to="/profile" className={linkStyle} onClick={() => setOpen(false)}>
        <Avatar url={user.avatarUrl} name={user.displayName} size={24} />
        {user.displayName}
      </NavLink>
      <NavLink to="/settings" className={linkStyle} onClick={() => setOpen(false)}>
        <PixelIcon name="gear" scale={1} />
        {t("nav.settings")}
      </NavLink>
      <button onClick={doLogout} className={linkStyle({ isActive: false })}>
        <PixelIcon name="logout" scale={1} />
        {t("nav.logout")}
      </button>
    </>
  ) : (
    <>
      <NavLink to="/login" className={linkStyle} onClick={() => setOpen(false)}>
        {t("nav.login")}
      </NavLink>
      <NavLink
        to="/register"
        onClick={() => setOpen(false)}
        className="border border-acc bg-acc px-3 py-1.5 font-bold text-accfg shadow-ring"
      >
        {t("nav.register")}
      </NavLink>
    </>
  );

  return (
    <header className="border-b border-line bg-surf">
      <div className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-3">
        <Link to="/" aria-label={t("nav.home")}>
          <Logo />
        </Link>
        <nav className="ml-auto hidden items-center gap-2 sm:flex">
          {links}
          <LangSwitch />
        </nav>
        <button
          className="ml-auto p-2 text-fg sm:hidden"
          aria-expanded={open}
          aria-label={open ? t("nav.close") : t("nav.menu")}
          onClick={() => setOpen(!open)}
        >
          <PixelIcon name={open ? "close" : "menu"} scale={2} />
        </button>
      </div>
      {open && (
        <nav className="flex flex-col gap-1 border-t border-line px-4 py-3 sm:hidden">
          {links}
          <div className="pt-2">
            <LangSwitch />
          </div>
        </nav>
      )}
    </header>
  );
}
