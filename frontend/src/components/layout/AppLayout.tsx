import { useTranslation } from "react-i18next";
import { Outlet } from "react-router";
import { Header } from "@/components/layout/Header";
import { useAuth } from "@/hooks/useAuth";

// wspolny uklad stron: pasek u gory i tresc
export function AppLayout() {
  const { loading } = useAuth();
  const { t } = useTranslation();
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        {loading ? <p className="pixel text-mut">{t("loading")}</p> : <Outlet />}
      </main>
    </div>
  );
}
