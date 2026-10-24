import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router";
import { login, resendVerification } from "@/api/auth";
import { ApiError } from "@/api/client";
import { FormPage } from "@/components/layout/FormPage";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { useAuth } from "@/hooks/useAuth";
import { errorText } from "@/lib/errors";
import * as check from "@/lib/validate";

export function LoginPage() {
  const { t } = useTranslation("auth");
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [notVerified, setNotVerified] = useState(false);
  const [resent, setResent] = useState(false);
  const [busy, setBusy] = useState(false);

  // wysyla formularz logowania
  async function submit(e: FormEvent) {
    e.preventDefault();
    const found = check.onlyErrors({ email: check.email(email), pass: check.required(pass) });
    setErrs(found);
    if (Object.keys(found).length) return;

    setBusy(true);
    setError("");
    try {
      setUser(await login(email.trim(), pass));
      const next = params.get("next");
      navigate(next?.startsWith("/") ? next : "/");
    } catch (err) {
      setNotVerified(err instanceof ApiError && err.code === "email_not_verified");
      setError(errorText(err));
    }
    setBusy(false);
  }

  async function resend() {
    await resendVerification(email.trim()).catch(() => null);
    setResent(true);
  }

  return (
    <FormPage
      title={t("login.title")}
      footer={
        <>
          <Link to="/forgot-password" className="hover:text-fg">
            {t("login.forgot")}
          </Link>
          <span>
            {t("login.noAccount")}{" "}
            <Link to="/register" className="text-acc hover:underline">
              {t("register.submit")}
            </Link>
          </span>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        <Field
          label={t("fields.email")}
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errs.email && t(errs.email)}
        />
        <Field
          label={t("fields.password")}
          type="password"
          autoComplete="current-password"
          value={pass}
          onChange={(e) => setPass(e.target.value)}
          error={errs.pass && t(errs.pass)}
        />
        {error && <Notice kind="error">{error}</Notice>}
        {notVerified &&
          (resent ? (
            <Notice kind="ok">{t("login.resent")}</Notice>
          ) : (
            <Button type="button" variant="secondary" onClick={resend}>
              {t("login.resend")}
            </Button>
          ))}
        <Button type="submit" busy={busy}>
          {t("login.submit")}
        </Button>
      </form>
    </FormPage>
  );
}
