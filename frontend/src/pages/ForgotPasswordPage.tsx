import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { forgotPassword } from "@/api/auth";
import { FormPage } from "@/components/layout/FormPage";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import * as check from "@/lib/validate";

export function ForgotPasswordPage() {
  const { t } = useTranslation("auth");
  const [email, setEmail] = useState("");
  const [emailErr, setEmailErr] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  // prosi o link do resetu (odpowiedz jest taka sama, czy konto istnieje, czy nie)
  async function submit(e: FormEvent) {
    e.preventDefault();
    const bad = check.email(email);
    setEmailErr(bad ? t(bad) : "");
    if (bad) return;
    setBusy(true);
    setError("");
    try {
      await forgotPassword(email.trim());
      setDone(true);
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  return (
    <FormPage
      title={t("forgot.title")}
      footer={
        <Link to="/login" className="hover:text-fg">
          {t("login.submit")}
        </Link>
      }
    >
      {done ? (
        <Notice kind="ok">{t("forgot.done")}</Notice>
      ) : (
        <form onSubmit={submit} noValidate className="flex flex-col gap-4">
          <p className="text-mut">{t("forgot.lead")}</p>
          <Field
            label={t("fields.email")}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={emailErr}
          />
          {error && <Notice kind="error">{error}</Notice>}
          <Button type="submit" busy={busy}>
            {t("forgot.submit")}
          </Button>
        </form>
      )}
    </FormPage>
  );
}
