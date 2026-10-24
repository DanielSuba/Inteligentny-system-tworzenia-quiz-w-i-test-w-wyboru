import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { useAuth } from "@/hooks/useAuth";

// strona startowa; quizy pojawia sie tu w etapie 2
export function HomePage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  return (
    <section className="flex max-w-2xl flex-col gap-5 border-t border-line pt-6">
      {user && <p className="pixel text-acc">{t("home.hello", { name: user.displayName })}</p>}
      <h1 className="text-3xl font-bold text-balance sm:text-4xl">{t("home.title")}</h1>
      <p className="text-lg text-mut">{t("home.lead")}</p>
      {user ? (
        <>
          <p className="text-mut">{t("home.soon")}</p>
          <Link to="/profile" className="self-start text-acc hover:underline">
            {t("home.toProfile")}
          </Link>
        </>
      ) : (
        <div className="flex flex-wrap gap-3">
          <Link
            to="/register"
            className="border border-acc bg-acc px-4 py-2 font-bold text-accfg shadow-ring"
          >
            {t("nav.register")}
          </Link>
          <Link to="/login" className="border border-line bg-surf2 px-4 py-2 font-bold shadow-ring">
            {t("nav.login")}
          </Link>
        </div>
      )}
    </section>
  );
}
