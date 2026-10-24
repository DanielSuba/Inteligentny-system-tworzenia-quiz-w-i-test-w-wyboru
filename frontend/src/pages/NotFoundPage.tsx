import { useTranslation } from "react-i18next";
import { Link } from "react-router";

export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <section className="flex flex-col gap-4 border-t border-line pt-6">
      <p className="font-pixel text-[36px] leading-none text-acc">404</p>
      <h1 className="text-xl font-bold">{t("notFound.title")}</h1>
      <Link to="/" className="text-acc hover:underline">
        {t("notFound.back")}
      </Link>
    </section>
  );
}
